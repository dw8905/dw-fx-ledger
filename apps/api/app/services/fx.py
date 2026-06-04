from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.fx import FxBuyLot, FxLotAllocation, FxLotEvent, FxSellTransaction
from app.schemas.fx import (
    BuyLotListResponse,
    BuyLotRead,
    LotAllocationRead,
    LotEventListResponse,
    LotEventRead,
    SellTransactionListItem,
    SellTransactionListResponse,
    SellTransactionRead,
)

OPEN = "open"
SPLIT = "split"
SOLD = "sold"
CANCELLED = "cancelled"
COMPLETED = "completed"
COMPLETED_EVENT = "completed"
SELL_TRANSACTION_CREATED = "sell_transaction_created"
LOT_SPLIT = "lot_split"
SELL_TRANSACTION_CANCELLED = "sell_transaction_cancelled"
LOT_RESTORED = "lot_restored"
NUMERIC_SCALE = Decimal("0.000001")
MIN_USD_AMOUNT = Decimal("0.000001")
BUY_LOT_SORT_COLUMNS = {
    "buy_date": FxBuyLot.buy_date,
    "buy_exchange_rate": FxBuyLot.buy_exchange_rate,
    "usd_amount": FxBuyLot.usd_amount,
    "buy_krw_amount": FxBuyLot.buy_krw_amount,
    "created_at": FxBuyLot.created_at,
    "lot_status": FxBuyLot.lot_status,
}
SELL_TRANSACTION_SORT_COLUMNS = {
    "sell_date": FxSellTransaction.sell_date,
    "sell_exchange_rate": FxSellTransaction.sell_exchange_rate,
    "sell_usd_amount": FxSellTransaction.sell_usd_amount,
    "total_real_profit_krw": FxSellTransaction.total_real_profit_krw,
    "total_display_profit_krw": FxSellTransaction.total_display_profit_krw,
    "created_at": FxSellTransaction.created_at,
    "transaction_status": FxSellTransaction.transaction_status,
}


class InsufficientBuyLotBalanceError(ValueError):
    pass


@dataclass(frozen=True)
class AllocationPlan:
    source_lot: FxBuyLot
    allocated_usd_amount: Decimal
    allocated_buy_krw_amount: int
    allocated_sell_krw_amount: int
    real_profit_krw: int
    display_profit_krw: int
    exchange_diff: Decimal
    remaining_usd_amount: Decimal
    remaining_buy_krw_amount: int


def quantize_numeric(value: Decimal) -> Decimal:
    return value.quantize(NUMERIC_SCALE, rounding=ROUND_HALF_UP)


def calculate_usd_amount(buy_krw_amount: int, buy_exchange_rate: Decimal) -> Decimal:
    return quantize_numeric(Decimal(buy_krw_amount) / buy_exchange_rate)


def calculate_sell_krw_amount(buy_krw_amount: int, sell_exchange_rate: Decimal, buy_exchange_rate: Decimal) -> int:
    return int((Decimal(buy_krw_amount) * sell_exchange_rate / buy_exchange_rate).to_integral_value(rounding=ROUND_CEILING))


def calculate_allocated_buy_krw_amount(source_lot: FxBuyLot, allocated_usd_amount: Decimal) -> int:
    if allocated_usd_amount == source_lot.usd_amount:
        return source_lot.buy_krw_amount

    return int((allocated_usd_amount * source_lot.buy_exchange_rate).to_integral_value(rounding=ROUND_CEILING))


def decimal_to_payload(value: Decimal) -> str:
    return format(value, "f")


def create_lot_event(
    db: Session,
    *,
    current_user: User,
    event_type: str,
    root_buy_lot_id: int | None = None,
    sell_transaction_id: int | None = None,
    lot_allocation_id: int | None = None,
    source_buy_lot_id: int | None = None,
    closed_buy_lot_id: int | None = None,
    remaining_buy_lot_id: int | None = None,
    restored_buy_lot_id: int | None = None,
    related_event_id: int | None = None,
    event_payload: dict | None = None,
) -> FxLotEvent:
    event = FxLotEvent(
        user_id=current_user.user_id,
        event_type=event_type,
        event_status=COMPLETED_EVENT,
        root_buy_lot_id=root_buy_lot_id,
        sell_transaction_id=sell_transaction_id,
        lot_allocation_id=lot_allocation_id,
        source_buy_lot_id=source_buy_lot_id,
        closed_buy_lot_id=closed_buy_lot_id,
        remaining_buy_lot_id=remaining_buy_lot_id,
        restored_buy_lot_id=restored_buy_lot_id,
        related_event_id=related_event_id,
        event_payload=event_payload,
        created_by=current_user.user_id,
    )
    db.add(event)
    db.flush()
    return event


def normalize_sort_order(sort_order: str | None) -> str | None:
    if sort_order is None:
        return None

    lowered = sort_order.lower()
    if lowered not in {"asc", "desc"}:
        raise ValueError("Invalid sort_order")

    return lowered


def apply_sort(query, *, columns, sort_by: str | None, sort_order: str | None, default_columns):
    normalized_order = normalize_sort_order(sort_order)
    if sort_by is None or normalized_order is None:
        return query.order_by(*default_columns)

    sort_column = columns.get(sort_by)
    if sort_column is None:
        raise ValueError("Invalid sort_by")

    direction = asc if normalized_order == "asc" else desc
    return query.order_by(direction(sort_column), desc(columns.get("created_at", FxBuyLot.created_at)))


def create_buy_lot(
    db: Session,
    *,
    current_user: User,
    buy_date,
    buy_krw_amount: int,
    buy_exchange_rate: Decimal,
) -> BuyLotRead:
    normalized_rate = quantize_numeric(buy_exchange_rate)
    buy_lot = FxBuyLot(
        user_id=current_user.user_id,
        lot_status=OPEN,
        buy_date=buy_date,
        buy_krw_amount=buy_krw_amount,
        buy_exchange_rate=normalized_rate,
        usd_amount=calculate_usd_amount(buy_krw_amount, normalized_rate),
        is_active=True,
        is_deleted=False,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    db.add(buy_lot)
    db.flush()
    buy_lot.root_buy_lot_id = buy_lot.buy_lot_id
    db.flush()
    db.refresh(buy_lot)
    return to_buy_lot_read(buy_lot)


def update_buy_lot(
    db: Session,
    *,
    current_user: User,
    buy_lot_id: int,
    buy_date,
    buy_krw_amount: int,
    buy_exchange_rate: Decimal,
) -> BuyLotRead | None:
    buy_lot = db.scalar(
        select(FxBuyLot).where(
            FxBuyLot.buy_lot_id == buy_lot_id,
            FxBuyLot.user_id == current_user.user_id,
            FxBuyLot.is_deleted.is_(False),
        )
    )
    if buy_lot is None:
        return None

    if buy_lot.lot_status != OPEN or not buy_lot.is_active:
        raise ValueError("Only active open buy lots can be updated")

    normalized_rate = quantize_numeric(buy_exchange_rate)
    buy_lot.buy_date = buy_date
    buy_lot.buy_krw_amount = buy_krw_amount
    buy_lot.buy_exchange_rate = normalized_rate
    buy_lot.usd_amount = calculate_usd_amount(buy_krw_amount, normalized_rate)
    buy_lot.updated_by = current_user.user_id
    buy_lot.lock_version += 1
    db.flush()
    db.refresh(buy_lot)
    return to_buy_lot_read(buy_lot)


def _buy_lots_query(user_id: int) -> Select[tuple[FxBuyLot]]:
    return select(FxBuyLot).where(FxBuyLot.user_id == user_id, FxBuyLot.is_deleted.is_(False))


def list_buy_lots(
    db: Session,
    *,
    current_user: User,
    page: int,
    size: int,
    lot_status: str | None,
    is_active: bool | None,
    sort_by: str | None,
    sort_order: str | None,
) -> BuyLotListResponse:
    query = _buy_lots_query(current_user.user_id)
    count_query = select(func.count()).select_from(FxBuyLot).where(
        FxBuyLot.user_id == current_user.user_id,
        FxBuyLot.is_deleted.is_(False),
    )

    if lot_status is not None:
        query = query.where(FxBuyLot.lot_status == lot_status)
        count_query = count_query.where(FxBuyLot.lot_status == lot_status)

    if is_active is not None:
        query = query.where(FxBuyLot.is_active.is_(is_active))
        count_query = count_query.where(FxBuyLot.is_active.is_(is_active))

    total_count = db.scalar(count_query) or 0
    try:
        query = apply_sort(
            query,
            columns=BUY_LOT_SORT_COLUMNS,
            sort_by=sort_by,
            sort_order=sort_order,
            default_columns=(FxBuyLot.created_at.desc(), FxBuyLot.buy_lot_id.desc()),
        )
    except ValueError as error:
        raise error

    buy_lots = db.scalars(query.offset((page - 1) * size).limit(size)).all()

    return BuyLotListResponse(
        items=[to_buy_lot_read(buy_lot) for buy_lot in buy_lots],
        page=page,
        size=size,
        totalCount=total_count,
    )


def get_buy_lot(db: Session, *, current_user: User, buy_lot_id: int) -> BuyLotRead | None:
    buy_lot = db.scalar(
        _buy_lots_query(current_user.user_id).where(FxBuyLot.buy_lot_id == buy_lot_id)
    )
    if buy_lot is None:
        return None

    return to_buy_lot_read(buy_lot)


def to_buy_lot_read(buy_lot: FxBuyLot) -> BuyLotRead:
    return BuyLotRead(
        buyLotId=buy_lot.buy_lot_id,
        buyDate=buy_lot.buy_date,
        buyKrwAmount=buy_lot.buy_krw_amount,
        buyExchangeRate=buy_lot.buy_exchange_rate,
        usdAmount=buy_lot.usd_amount,
        lotStatus=buy_lot.lot_status,
        isActive=buy_lot.is_active,
        createdAt=buy_lot.created_at,
    )


def get_source_lots_for_strategy(db: Session, *, user_id: int, strategy: str) -> list[FxBuyLot]:
    query = (
        select(FxBuyLot)
        .where(
            FxBuyLot.user_id == user_id,
            FxBuyLot.is_deleted.is_(False),
            FxBuyLot.is_active.is_(True),
            FxBuyLot.lot_status == OPEN,
        )
        .with_for_update()
    )

    if strategy == "highest_rate_first":
        query = query.order_by(FxBuyLot.buy_exchange_rate.desc(), FxBuyLot.buy_date.asc(), FxBuyLot.buy_lot_id.asc())
    elif strategy == "fifo":
        query = query.order_by(FxBuyLot.buy_date.asc(), FxBuyLot.buy_lot_id.asc())
    elif strategy == "lifo":
        query = query.order_by(FxBuyLot.buy_date.desc(), FxBuyLot.buy_lot_id.desc())
    else:
        raise ValueError("Invalid allocation strategy")

    return list(db.scalars(query).all())


def build_allocation_plans(
    *,
    source_lots: list[FxBuyLot],
    sell_usd_amount: Decimal,
    sell_exchange_rate: Decimal,
) -> list[AllocationPlan]:
    remaining_to_sell = quantize_numeric(sell_usd_amount)
    normalized_sell_rate = quantize_numeric(sell_exchange_rate)
    plans: list[AllocationPlan] = []

    for source_lot in source_lots:
        if remaining_to_sell <= 0:
            break

        allocated_usd = min(source_lot.usd_amount, remaining_to_sell)
        allocated_usd = quantize_numeric(allocated_usd)
        allocated_buy_krw = calculate_allocated_buy_krw_amount(source_lot, allocated_usd)
        allocated_sell_krw = calculate_sell_krw_amount(
            allocated_buy_krw,
            normalized_sell_rate,
            source_lot.buy_exchange_rate,
        )
        real_profit = allocated_sell_krw - allocated_buy_krw
        remaining_usd = quantize_numeric(source_lot.usd_amount - allocated_usd)
        remaining_buy_krw = source_lot.buy_krw_amount - allocated_buy_krw
        exchange_diff = max(normalized_sell_rate - source_lot.buy_exchange_rate, Decimal("0"))

        plans.append(
            AllocationPlan(
                source_lot=source_lot,
                allocated_usd_amount=allocated_usd,
                allocated_buy_krw_amount=allocated_buy_krw,
                allocated_sell_krw_amount=allocated_sell_krw,
                real_profit_krw=real_profit,
                display_profit_krw=max(real_profit, 0),
                exchange_diff=quantize_numeric(exchange_diff),
                remaining_usd_amount=remaining_usd,
                remaining_buy_krw_amount=remaining_buy_krw,
            )
        )
        remaining_to_sell = quantize_numeric(remaining_to_sell - allocated_usd)

    if remaining_to_sell > 0:
        raise InsufficientBuyLotBalanceError("Not enough open buy lot balance")

    return plans


def create_sell_transaction(
    db: Session,
    *,
    current_user: User,
    sell_date: date,
    sell_usd_amount: Decimal,
    sell_exchange_rate: Decimal,
    allocation_strategy: str,
    memo: str | None,
) -> SellTransactionRead:
    normalized_sell_usd = quantize_numeric(sell_usd_amount)
    normalized_sell_rate = quantize_numeric(sell_exchange_rate)
    source_lots = get_source_lots_for_strategy(
        db,
        user_id=current_user.user_id,
        strategy=allocation_strategy,
    )
    plans = build_allocation_plans(
        source_lots=source_lots,
        sell_usd_amount=normalized_sell_usd,
        sell_exchange_rate=normalized_sell_rate,
    )

    transaction = FxSellTransaction(
        user_id=current_user.user_id,
        sell_date=sell_date,
        sell_usd_amount=normalized_sell_usd,
        sell_exchange_rate=normalized_sell_rate,
        allocation_strategy=allocation_strategy,
        transaction_status=COMPLETED,
        total_buy_krw_amount=sum(plan.allocated_buy_krw_amount for plan in plans),
        total_sell_krw_amount=sum(plan.allocated_sell_krw_amount for plan in plans),
        total_real_profit_krw=sum(plan.real_profit_krw for plan in plans),
        total_display_profit_krw=sum(plan.display_profit_krw for plan in plans),
        memo=memo,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    db.add(transaction)
    db.flush()

    create_lot_event(
        db,
        current_user=current_user,
        event_type=SELL_TRANSACTION_CREATED,
        sell_transaction_id=transaction.sell_transaction_id,
        event_payload={
            "sellDate": sell_date.isoformat(),
            "sellUsdAmount": decimal_to_payload(normalized_sell_usd),
            "sellExchangeRate": decimal_to_payload(normalized_sell_rate),
            "allocationStrategy": allocation_strategy,
            "memo": memo,
        },
    )

    allocations: list[FxLotAllocation] = []
    for plan in plans:
        root_buy_lot_id = plan.source_lot.root_buy_lot_id or plan.source_lot.buy_lot_id
        plan.source_lot.lot_status = SPLIT
        plan.source_lot.is_active = False
        plan.source_lot.updated_by = current_user.user_id
        plan.source_lot.lock_version += 1

        sold_lot = FxBuyLot(
            user_id=current_user.user_id,
            parent_buy_lot_id=plan.source_lot.buy_lot_id,
            root_buy_lot_id=root_buy_lot_id,
            lot_status=SOLD,
            buy_date=plan.source_lot.buy_date,
            buy_krw_amount=plan.allocated_buy_krw_amount,
            buy_exchange_rate=plan.source_lot.buy_exchange_rate,
            usd_amount=plan.allocated_usd_amount,
            is_active=False,
            is_deleted=False,
            created_by=current_user.user_id,
            updated_by=current_user.user_id,
        )
        db.add(sold_lot)
        db.flush()

        remaining_lot_id = None
        if plan.remaining_usd_amount >= MIN_USD_AMOUNT and plan.remaining_buy_krw_amount > 0:
            remaining_lot = FxBuyLot(
                user_id=current_user.user_id,
                parent_buy_lot_id=plan.source_lot.buy_lot_id,
                root_buy_lot_id=root_buy_lot_id,
                lot_status=OPEN,
                buy_date=plan.source_lot.buy_date,
                buy_krw_amount=plan.remaining_buy_krw_amount,
                buy_exchange_rate=plan.source_lot.buy_exchange_rate,
                usd_amount=plan.remaining_usd_amount,
                is_active=True,
                is_deleted=False,
                created_by=current_user.user_id,
                updated_by=current_user.user_id,
            )
            db.add(remaining_lot)
            db.flush()
            remaining_lot_id = remaining_lot.buy_lot_id

        allocation = FxLotAllocation(
            sell_transaction_id=transaction.sell_transaction_id,
            source_buy_lot_id=plan.source_lot.buy_lot_id,
            closed_buy_lot_id=sold_lot.buy_lot_id,
            remaining_buy_lot_id=remaining_lot_id,
            allocated_usd_amount=plan.allocated_usd_amount,
            allocated_buy_krw_amount=plan.allocated_buy_krw_amount,
            allocated_sell_krw_amount=plan.allocated_sell_krw_amount,
            real_profit_krw=plan.real_profit_krw,
            display_profit_krw=plan.display_profit_krw,
            exchange_diff=plan.exchange_diff,
            created_by=current_user.user_id,
        )
        db.add(allocation)
        db.flush()
        create_lot_event(
            db,
            current_user=current_user,
            event_type=LOT_SPLIT,
            root_buy_lot_id=root_buy_lot_id,
            sell_transaction_id=transaction.sell_transaction_id,
            lot_allocation_id=allocation.lot_allocation_id,
            source_buy_lot_id=plan.source_lot.buy_lot_id,
            closed_buy_lot_id=sold_lot.buy_lot_id,
            remaining_buy_lot_id=remaining_lot_id,
            event_payload={
                "allocatedUsdAmount": decimal_to_payload(plan.allocated_usd_amount),
                "buyRate": decimal_to_payload(plan.source_lot.buy_exchange_rate),
                "sellRate": decimal_to_payload(normalized_sell_rate),
                "allocatedBuyKrwAmount": plan.allocated_buy_krw_amount,
                "allocatedSellKrwAmount": plan.allocated_sell_krw_amount,
                "realProfitKrw": plan.real_profit_krw,
                "displayProfitKrw": plan.display_profit_krw,
            },
        )
        allocations.append(allocation)

    db.flush()
    db.refresh(transaction)
    return to_sell_transaction_read(transaction, allocations)


def list_sell_transactions(
    db: Session,
    *,
    current_user: User,
    page: int,
    size: int,
    sort_by: str | None,
    sort_order: str | None,
) -> SellTransactionListResponse:
    query = select(FxSellTransaction).where(
        FxSellTransaction.user_id == current_user.user_id,
        FxSellTransaction.is_deleted.is_(False),
    )
    count_query = select(func.count()).select_from(FxSellTransaction).where(
        FxSellTransaction.user_id == current_user.user_id,
        FxSellTransaction.is_deleted.is_(False),
    )
    query = apply_sort(
        query,
        columns=SELL_TRANSACTION_SORT_COLUMNS,
        sort_by=sort_by,
        sort_order=sort_order,
        default_columns=(FxSellTransaction.created_at.desc(), FxSellTransaction.sell_transaction_id.desc()),
    )
    rows = db.scalars(query.offset((page - 1) * size).limit(size)).all()
    return SellTransactionListResponse(
        items=[to_sell_transaction_list_item(row) for row in rows],
        page=page,
        size=size,
        totalCount=db.scalar(count_query) or 0,
    )


def get_sell_transaction(
    db: Session,
    *,
    current_user: User,
    sell_transaction_id: int,
) -> SellTransactionRead | None:
    transaction = db.scalar(
        select(FxSellTransaction).where(
            FxSellTransaction.sell_transaction_id == sell_transaction_id,
            FxSellTransaction.user_id == current_user.user_id,
            FxSellTransaction.is_deleted.is_(False),
        )
    )
    if transaction is None:
        return None

    allocations = list(
        db.scalars(
            select(FxLotAllocation).where(
                FxLotAllocation.sell_transaction_id == transaction.sell_transaction_id
            )
        ).all()
    )
    return to_sell_transaction_read(transaction, allocations)


def cancel_sell_transaction(
    db: Session,
    *,
    current_user: User,
    sell_transaction_id: int,
    cancel_reason: str,
) -> SellTransactionRead | None:
    transaction = db.scalar(
        select(FxSellTransaction)
        .where(
            FxSellTransaction.sell_transaction_id == sell_transaction_id,
            FxSellTransaction.user_id == current_user.user_id,
            FxSellTransaction.is_deleted.is_(False),
        )
        .with_for_update()
    )
    if transaction is None:
        return None

    if transaction.transaction_status != COMPLETED:
        raise ValueError("Only completed sell transactions can be cancelled")

    allocations = list(
        db.scalars(
            select(FxLotAllocation)
            .where(FxLotAllocation.sell_transaction_id == sell_transaction_id)
            .with_for_update()
        ).all()
    )
    if not allocations:
        raise ValueError("Sell transaction has no allocations")

    remaining_ids = [
        allocation.remaining_buy_lot_id
        for allocation in allocations
        if allocation.remaining_buy_lot_id is not None
    ]
    if remaining_ids:
        downstream_exists = db.scalar(
            select(func.count())
            .select_from(FxLotAllocation)
            .join(
                FxSellTransaction,
                FxSellTransaction.sell_transaction_id == FxLotAllocation.sell_transaction_id,
            )
            .where(
                FxLotAllocation.source_buy_lot_id.in_(remaining_ids),
                FxSellTransaction.transaction_status == COMPLETED,
                FxSellTransaction.user_id == current_user.user_id,
            )
        )
        if downstream_exists:
            raise ValueError("Only the latest sell transaction in a lot chain can be cancelled")

    transaction.transaction_status = CANCELLED
    transaction.updated_by = current_user.user_id
    cancellation_event = create_lot_event(
        db,
        current_user=current_user,
        event_type=SELL_TRANSACTION_CANCELLED,
        sell_transaction_id=transaction.sell_transaction_id,
        event_payload={"cancelReason": cancel_reason},
    )

    restored_allocations: list[FxLotAllocation] = []
    for allocation in allocations:
        source_lot = db.scalar(
            select(FxBuyLot)
            .where(
                FxBuyLot.buy_lot_id == allocation.source_buy_lot_id,
                FxBuyLot.user_id == current_user.user_id,
            )
            .with_for_update()
        )
        closed_lot = db.scalar(
            select(FxBuyLot)
            .where(
                FxBuyLot.buy_lot_id == allocation.closed_buy_lot_id,
                FxBuyLot.user_id == current_user.user_id,
            )
            .with_for_update()
        )
        remaining_lot = (
            db.scalar(
                select(FxBuyLot)
                .where(
                    FxBuyLot.buy_lot_id == allocation.remaining_buy_lot_id,
                    FxBuyLot.user_id == current_user.user_id,
                )
                .with_for_update()
            )
            if allocation.remaining_buy_lot_id is not None
            else None
        )
        if source_lot is None or closed_lot is None:
            raise ValueError("Allocation lot chain is incomplete")

        root_buy_lot_id = source_lot.root_buy_lot_id or source_lot.buy_lot_id
        closed_lot.lot_status = CANCELLED
        closed_lot.is_active = False
        closed_lot.updated_by = current_user.user_id
        closed_lot.lock_version += 1

        if remaining_lot is not None:
            remaining_lot.lot_status = CANCELLED
            remaining_lot.is_active = False
            remaining_lot.updated_by = current_user.user_id
            remaining_lot.lock_version += 1

        restored_lot = FxBuyLot(
            user_id=current_user.user_id,
            parent_buy_lot_id=source_lot.buy_lot_id,
            root_buy_lot_id=root_buy_lot_id,
            lot_status=OPEN,
            buy_date=source_lot.buy_date,
            buy_krw_amount=source_lot.buy_krw_amount,
            buy_exchange_rate=source_lot.buy_exchange_rate,
            usd_amount=source_lot.usd_amount,
            is_active=True,
            is_deleted=False,
            created_by=current_user.user_id,
            updated_by=current_user.user_id,
        )
        db.add(restored_lot)
        db.flush()
        create_lot_event(
            db,
            current_user=current_user,
            event_type=LOT_RESTORED,
            root_buy_lot_id=root_buy_lot_id,
            sell_transaction_id=transaction.sell_transaction_id,
            lot_allocation_id=allocation.lot_allocation_id,
            source_buy_lot_id=source_lot.buy_lot_id,
            closed_buy_lot_id=closed_lot.buy_lot_id,
            remaining_buy_lot_id=remaining_lot.buy_lot_id if remaining_lot else None,
            restored_buy_lot_id=restored_lot.buy_lot_id,
            related_event_id=cancellation_event.lot_event_id,
            event_payload={
                "cancelReason": cancel_reason,
                "restoredBuyKrwAmount": restored_lot.buy_krw_amount,
                "restoredUsdAmount": decimal_to_payload(restored_lot.usd_amount),
                "buyRate": decimal_to_payload(restored_lot.buy_exchange_rate),
            },
        )
        restored_allocations.append(allocation)

    db.flush()
    db.refresh(transaction)
    return to_sell_transaction_read(transaction, restored_allocations)


def list_lot_events(
    db: Session,
    *,
    current_user: User,
    page: int,
    size: int,
    root_buy_lot_id: int | None,
    sell_transaction_id: int | None,
) -> LotEventListResponse:
    query = select(FxLotEvent).where(FxLotEvent.user_id == current_user.user_id)
    count_query = select(func.count()).select_from(FxLotEvent).where(
        FxLotEvent.user_id == current_user.user_id
    )
    if root_buy_lot_id is not None:
        query = query.where(FxLotEvent.root_buy_lot_id == root_buy_lot_id)
        count_query = count_query.where(FxLotEvent.root_buy_lot_id == root_buy_lot_id)
    if sell_transaction_id is not None:
        query = query.where(FxLotEvent.sell_transaction_id == sell_transaction_id)
        count_query = count_query.where(FxLotEvent.sell_transaction_id == sell_transaction_id)

    events = db.scalars(
        query.order_by(FxLotEvent.created_at.desc(), FxLotEvent.lot_event_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return LotEventListResponse(
        items=[to_lot_event_read(event) for event in events],
        page=page,
        size=size,
        totalCount=db.scalar(count_query) or 0,
    )


def to_lot_allocation_read(allocation: FxLotAllocation) -> LotAllocationRead:
    return LotAllocationRead(
        lotAllocationId=allocation.lot_allocation_id,
        sourceBuyLotId=allocation.source_buy_lot_id,
        closedBuyLotId=allocation.closed_buy_lot_id,
        remainingBuyLotId=allocation.remaining_buy_lot_id,
        allocatedUsdAmount=allocation.allocated_usd_amount,
        allocatedBuyKrwAmount=allocation.allocated_buy_krw_amount,
        allocatedSellKrwAmount=allocation.allocated_sell_krw_amount,
        realProfitKrw=allocation.real_profit_krw,
        displayProfitKrw=allocation.display_profit_krw,
        exchangeDiff=allocation.exchange_diff,
    )


def to_sell_transaction_read(
    transaction: FxSellTransaction,
    allocations: list[FxLotAllocation],
) -> SellTransactionRead:
    return SellTransactionRead(
        sellTransactionId=transaction.sell_transaction_id,
        sellDate=transaction.sell_date,
        sellUsdAmount=transaction.sell_usd_amount,
        sellExchangeRate=transaction.sell_exchange_rate,
        allocationStrategy=transaction.allocation_strategy,
        transactionStatus=transaction.transaction_status,
        totalBuyKrwAmount=transaction.total_buy_krw_amount,
        totalSellKrwAmount=transaction.total_sell_krw_amount,
        totalRealProfitKrw=transaction.total_real_profit_krw,
        totalDisplayProfitKrw=transaction.total_display_profit_krw,
        memo=transaction.memo,
        createdAt=transaction.created_at,
        allocations=[to_lot_allocation_read(allocation) for allocation in allocations],
    )


def to_sell_transaction_list_item(transaction: FxSellTransaction) -> SellTransactionListItem:
    return SellTransactionListItem(
        sellTransactionId=transaction.sell_transaction_id,
        sellDate=transaction.sell_date,
        sellUsdAmount=transaction.sell_usd_amount,
        sellExchangeRate=transaction.sell_exchange_rate,
        allocationStrategy=transaction.allocation_strategy,
        transactionStatus=transaction.transaction_status,
        totalBuyKrwAmount=transaction.total_buy_krw_amount,
        totalSellKrwAmount=transaction.total_sell_krw_amount,
        totalRealProfitKrw=transaction.total_real_profit_krw,
        totalDisplayProfitKrw=transaction.total_display_profit_krw,
        memo=transaction.memo,
        createdAt=transaction.created_at,
    )


def to_lot_event_read(event: FxLotEvent) -> LotEventRead:
    return LotEventRead(
        lotEventId=event.lot_event_id,
        eventType=event.event_type,
        eventStatus=event.event_status,
        rootBuyLotId=event.root_buy_lot_id,
        sellTransactionId=event.sell_transaction_id,
        lotAllocationId=event.lot_allocation_id,
        sourceBuyLotId=event.source_buy_lot_id,
        closedBuyLotId=event.closed_buy_lot_id,
        remainingBuyLotId=event.remaining_buy_lot_id,
        restoredBuyLotId=event.restored_buy_lot_id,
        relatedEventId=event.related_event_id,
        eventPayload=event.event_payload,
        createdAt=event.created_at,
    )

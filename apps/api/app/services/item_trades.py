from datetime import UTC, datetime
from decimal import Decimal, ROUND_CEILING

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.item_trade import ItemCode, ItemTrade
from app.schemas.item_trades import (
    ItemCodeListResponse,
    ItemCodeRead,
    ItemCodeSummary,
    ItemTradeListResponse,
    ItemTradeRead,
)

BUY = "buy"
SELL = "sell"
ADJUSTMENT = "adjustment"
ACTIVE = "active"
CANCELLED = "cancelled"
FEE_SCALE = Decimal("0.000001")
DEFAULT_ITEM_SELL_FEE_RATE = Decimal("0.050000")


def quantize_fee_rate(value: Decimal) -> Decimal:
    return value.quantize(FEE_SCALE)


def ceil_divide(numerator: int | Decimal, denominator: int | Decimal) -> int:
    return int((Decimal(numerator) / Decimal(denominator)).to_integral_value(rounding=ROUND_CEILING))


def calculate_minimum_profitable_unit_price(buy_unit_price: int, fee_rate: Decimal) -> int:
    net_rate = Decimal("1") - fee_rate
    return int((Decimal(buy_unit_price) / net_rate).to_integral_value(rounding=ROUND_CEILING))


def calculate_fee_amount(total_sell_amount: int, fee_rate: Decimal) -> int:
    return int((Decimal(total_sell_amount) * fee_rate).to_integral_value(rounding=ROUND_CEILING))


def effective_inventory_fee_rate(fee_rate: Decimal | None) -> Decimal:
    if fee_rate is None or fee_rate <= 0:
        return DEFAULT_ITEM_SELL_FEE_RATE
    return fee_rate


def normalize_item_code(value: str) -> str:
    return value.strip()


def create_item_code(
    db: Session,
    *,
    current_user: User,
    item_code: str,
    item_name: str,
    memo: str | None = None,
) -> ItemCodeRead:
    normalized_code = normalize_item_code(item_code)
    existing = get_item_code_by_code(db, item_code=normalized_code, include_inactive=True)
    if existing is not None:
        raise ValueError("Item code already exists")

    code = ItemCode(
        user_id=None,
        item_code=normalized_code,
        item_name=item_name.strip(),
        memo=memo,
        is_active=True,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )
    db.add(code)
    db.flush()
    db.refresh(code)
    return to_item_code_read(code)


def ensure_item_code(
    db: Session,
    *,
    item_code: str,
    item_name: str,
) -> ItemCode:
    normalized_code = normalize_item_code(item_code)
    existing = get_item_code_by_code(db, item_code=normalized_code)
    if existing is not None:
        return existing

    raise ValueError("Item code not found")


def get_item_code_by_code(
    db: Session,
    *,
    item_code: str,
    include_inactive: bool = False,
) -> ItemCode | None:
    filters = [ItemCode.item_code == normalize_item_code(item_code), ItemCode.is_deleted.is_(False)]
    if not include_inactive:
        filters.append(ItemCode.is_active.is_(True))
    return db.scalar(select(ItemCode).where(*filters))


def list_item_codes(db: Session) -> ItemCodeListResponse:
    rows = db.scalars(
        select(ItemCode)
        .where(ItemCode.is_deleted.is_(False), ItemCode.is_active.is_(True))
        .order_by(ItemCode.item_name.asc(), ItemCode.item_code_id.asc())
    ).all()
    return ItemCodeListResponse(items=[to_item_code_read(row) for row in rows])


def get_latest_trade_for_code(db: Session, *, current_user: User, item_code_id: int) -> ItemTrade | None:
    return db.scalar(
        select(ItemTrade)
        .where(
            ItemTrade.user_id == current_user.user_id,
            ItemTrade.item_code_id == item_code_id,
            ItemTrade.is_deleted.is_(False),
            ItemTrade.trade_status == ACTIVE,
        )
        .order_by(ItemTrade.item_trade_id.desc())
        .limit(1)
    )


def create_item_trade(
    db: Session,
    *,
    current_user: User,
    item_code: str,
    item_name: str,
    trade_type: str,
    trade_date,
    unit_price: int,
    quantity: int,
    fee_rate: Decimal,
    memo: str | None = None,
) -> ItemTradeRead:
    if trade_type not in {BUY, SELL, ADJUSTMENT}:
        raise ValueError("Invalid trade_type")
    if trade_type in {BUY, SELL} and quantity <= 0:
        raise ValueError("Quantity must be positive")

    normalized_fee_rate = quantize_fee_rate(fee_rate)
    code = ensure_item_code(
        db,
        item_code=item_code,
        item_name=item_name,
    )
    latest_trade = get_latest_trade_for_code(db, current_user=current_user, item_code_id=code.item_code_id)
    current_quantity = latest_trade.inventory_quantity_after if latest_trade else 0
    current_value = latest_trade.inventory_value_after if latest_trade else 0

    if trade_type == BUY:
        trade = build_buy_trade(
            current_user=current_user,
            code=code,
            trade_date=trade_date,
            unit_price=unit_price,
            quantity=quantity,
            fee_rate=normalized_fee_rate,
            current_quantity=current_quantity or 0,
            current_value=current_value or 0,
            memo=memo,
        )
    elif trade_type == SELL:
        trade = build_sell_trade(
            current_user=current_user,
            code=code,
            trade_date=trade_date,
            unit_price=unit_price,
            quantity=quantity,
            fee_rate=normalized_fee_rate,
            current_quantity=current_quantity or 0,
            current_value=current_value or 0,
            memo=memo,
        )
    else:
        trade = build_adjustment_trade(
            current_user=current_user,
            code=code,
            trade_date=trade_date,
            unit_price=unit_price,
            quantity_delta=quantity,
            fee_rate=normalized_fee_rate,
            current_quantity=current_quantity or 0,
            current_value=current_value or 0,
            memo=memo,
        )

    db.add(trade)
    db.flush()
    db.refresh(trade)
    return to_item_trade_read(trade, code)


def build_buy_trade(
    *,
    current_user: User,
    code: ItemCode,
    trade_date,
    unit_price: int,
    quantity: int,
    fee_rate: Decimal,
    current_quantity: int,
    current_value: int,
    memo: str | None,
) -> ItemTrade:
    total_buy_amount = unit_price * quantity
    inventory_quantity_after = current_quantity + quantity
    inventory_value_after = current_value + total_buy_amount
    average_buy_unit_price = ceil_divide(inventory_value_after, inventory_quantity_after)
    minimum_profitable_unit_price = calculate_minimum_profitable_unit_price(
        average_buy_unit_price,
        fee_rate,
    )
    return ItemTrade(
        user_id=current_user.user_id,
        item_code_id=code.item_code_id,
        trade_type=BUY,
        trade_status=ACTIVE,
        item_name=code.item_name,
        buy_date=trade_date,
        buy_unit_price=unit_price,
        quantity=quantity,
        fee_rate=fee_rate,
        minimum_profitable_unit_price=minimum_profitable_unit_price,
        average_buy_unit_price=average_buy_unit_price,
        inventory_quantity_after=inventory_quantity_after,
        inventory_value_after=inventory_value_after,
        sell_date=None,
        sell_unit_price=None,
        total_buy_amount=total_buy_amount,
        total_sell_amount=None,
        fee_amount=None,
        net_sell_amount=None,
        profit_amount=None,
        memo=memo,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )


def build_sell_trade(
    *,
    current_user: User,
    code: ItemCode,
    trade_date,
    unit_price: int,
    quantity: int,
    fee_rate: Decimal,
    current_quantity: int,
    current_value: int,
    memo: str | None,
) -> ItemTrade:
    if current_quantity < quantity:
        raise ValueError("Not enough item inventory")

    average_buy_unit_price = ceil_divide(current_value, current_quantity)
    cost_basis = current_value if current_quantity == quantity else ceil_divide(current_value * quantity, current_quantity)
    total_sell_amount = unit_price * quantity
    fee_amount = calculate_fee_amount(total_sell_amount, fee_rate)
    net_sell_amount = total_sell_amount - fee_amount
    profit_amount = net_sell_amount - cost_basis
    inventory_quantity_after = current_quantity - quantity
    inventory_value_after = 0 if inventory_quantity_after == 0 else current_value - cost_basis
    minimum_profitable_unit_price = calculate_minimum_profitable_unit_price(
        average_buy_unit_price,
        fee_rate,
    )
    return ItemTrade(
        user_id=current_user.user_id,
        item_code_id=code.item_code_id,
        trade_type=SELL,
        trade_status=ACTIVE,
        item_name=code.item_name,
        buy_date=trade_date,
        buy_unit_price=average_buy_unit_price,
        quantity=quantity,
        fee_rate=fee_rate,
        minimum_profitable_unit_price=minimum_profitable_unit_price,
        average_buy_unit_price=average_buy_unit_price,
        inventory_quantity_after=inventory_quantity_after,
        inventory_value_after=inventory_value_after,
        sell_date=trade_date,
        sell_unit_price=unit_price,
        total_buy_amount=cost_basis,
        total_sell_amount=total_sell_amount,
        fee_amount=fee_amount,
        net_sell_amount=net_sell_amount,
        profit_amount=profit_amount,
        memo=memo,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )


def build_adjustment_trade(
    *,
    current_user: User,
    code: ItemCode,
    trade_date,
    unit_price: int,
    quantity_delta: int,
    fee_rate: Decimal,
    current_quantity: int,
    current_value: int,
    memo: str | None,
) -> ItemTrade:
    if quantity_delta == 0:
        raise ValueError("Adjustment quantity must not be zero")
    if current_quantity + quantity_delta < 0:
        raise ValueError("Adjustment would make item inventory negative")

    effective_unit_price = (
        ceil_divide(current_value, current_quantity)
        if quantity_delta < 0 and current_quantity and current_value
        else unit_price
    )
    adjustment_value = effective_unit_price * quantity_delta
    inventory_quantity_after = current_quantity + quantity_delta
    inventory_value_after = current_value + adjustment_value
    if inventory_quantity_after == 0:
        inventory_value_after = 0
    average_buy_unit_price = (
        ceil_divide(inventory_value_after, inventory_quantity_after)
        if inventory_quantity_after and inventory_value_after
        else 0
    )
    minimum_profitable_unit_price = (
        calculate_minimum_profitable_unit_price(average_buy_unit_price, effective_inventory_fee_rate(fee_rate))
        if average_buy_unit_price
        else 0
    )
    return ItemTrade(
        user_id=current_user.user_id,
        item_code_id=code.item_code_id,
        trade_type=ADJUSTMENT,
        trade_status=ACTIVE,
        item_name=code.item_name,
        buy_date=trade_date,
        buy_unit_price=effective_unit_price,
        quantity=quantity_delta,
        fee_rate=fee_rate,
        minimum_profitable_unit_price=minimum_profitable_unit_price,
        average_buy_unit_price=average_buy_unit_price,
        inventory_quantity_after=inventory_quantity_after,
        inventory_value_after=inventory_value_after,
        sell_date=None,
        sell_unit_price=None,
        total_buy_amount=adjustment_value,
        total_sell_amount=None,
        fee_amount=None,
        net_sell_amount=None,
        profit_amount=None,
        memo=memo,
        created_by=current_user.user_id,
        updated_by=current_user.user_id,
    )


def recalculate_item_trades_for_code(
    db: Session,
    *,
    current_user: User,
    item_code_id: int,
) -> None:
    trades = db.scalars(
        select(ItemTrade)
        .where(
            ItemTrade.user_id == current_user.user_id,
            ItemTrade.item_code_id == item_code_id,
            ItemTrade.is_deleted.is_(False),
        )
        .order_by(ItemTrade.item_trade_id.asc())
        .with_for_update()
    ).all()
    current_quantity = 0
    current_value = 0

    for trade in trades:
        if trade.trade_status == CANCELLED:
            continue

        if trade.trade_type == BUY:
            total_buy_amount = trade.buy_unit_price * trade.quantity
            current_quantity += trade.quantity
            current_value += total_buy_amount
            average_buy_unit_price = ceil_divide(current_value, current_quantity)
            trade.total_buy_amount = total_buy_amount
            trade.total_sell_amount = None
            trade.fee_amount = None
            trade.net_sell_amount = None
            trade.profit_amount = None
        elif trade.trade_type == SELL:
            if current_quantity < trade.quantity:
                raise ValueError("Cancellation would make item inventory negative")

            average_buy_unit_price = ceil_divide(current_value, current_quantity)
            cost_basis = (
                current_value
                if current_quantity == trade.quantity
                else ceil_divide(current_value * trade.quantity, current_quantity)
            )
            total_sell_amount = (trade.sell_unit_price or 0) * trade.quantity
            fee_amount = calculate_fee_amount(total_sell_amount, trade.fee_rate)
            net_sell_amount = total_sell_amount - fee_amount
            trade.buy_unit_price = average_buy_unit_price
            trade.total_buy_amount = cost_basis
            trade.total_sell_amount = total_sell_amount
            trade.fee_amount = fee_amount
            trade.net_sell_amount = net_sell_amount
            trade.profit_amount = net_sell_amount - cost_basis
            current_quantity -= trade.quantity
            current_value = 0 if current_quantity == 0 else current_value - cost_basis
        else:
            if current_quantity + trade.quantity < 0:
                raise ValueError("Adjustment would make item inventory negative")
            effective_unit_price = (
                ceil_divide(current_value, current_quantity)
                if trade.quantity < 0 and current_quantity and current_value
                else trade.buy_unit_price
            )
            adjustment_value = effective_unit_price * trade.quantity
            current_quantity += trade.quantity
            current_value += adjustment_value
            if current_quantity == 0:
                current_value = 0
            average_buy_unit_price = ceil_divide(current_value, current_quantity) if current_quantity and current_value else 0
            trade.buy_unit_price = effective_unit_price
            trade.total_buy_amount = adjustment_value
            trade.total_sell_amount = None
            trade.fee_amount = None
            trade.net_sell_amount = None
            trade.profit_amount = None

        trade.average_buy_unit_price = average_buy_unit_price
        trade.minimum_profitable_unit_price = calculate_minimum_profitable_unit_price(
            average_buy_unit_price,
            effective_inventory_fee_rate(trade.fee_rate),
        ) if average_buy_unit_price else 0
        trade.inventory_quantity_after = current_quantity
        trade.inventory_value_after = current_value
        trade.updated_by = current_user.user_id


def cancel_item_trade(
    db: Session,
    *,
    current_user: User,
    item_trade_id: int,
    cancel_reason: str | None,
) -> ItemTradeRead | None:
    trade = db.scalar(
        select(ItemTrade)
        .where(
            ItemTrade.item_trade_id == item_trade_id,
            ItemTrade.user_id == current_user.user_id,
            ItemTrade.is_deleted.is_(False),
        )
        .with_for_update()
    )
    if trade is None:
        return None
    if trade.trade_status == CANCELLED:
        raise ValueError("Item trade is already cancelled")
    if trade.item_code_id is None:
        raise ValueError("Item trade has no item code")

    trade.trade_status = CANCELLED
    trade.cancelled_at = datetime.now(UTC)
    trade.cancel_reason = cancel_reason
    trade.inventory_quantity_after = None
    trade.inventory_value_after = None
    trade.updated_by = current_user.user_id
    try:
        recalculate_item_trades_for_code(db, current_user=current_user, item_code_id=trade.item_code_id)
    except ValueError:
        trade.trade_status = ACTIVE
        trade.cancelled_at = None
        trade.cancel_reason = None
        raise

    db.flush()
    code = db.scalar(select(ItemCode).where(ItemCode.item_code_id == trade.item_code_id))
    db.refresh(trade)
    return to_item_trade_read(trade, code)


def list_item_trades(
    db: Session,
    *,
    current_user: User,
    page: int,
    size: int,
) -> ItemTradeListResponse:
    filters = [ItemTrade.user_id == current_user.user_id, ItemTrade.is_deleted.is_(False)]
    rows = db.execute(
        select(ItemTrade, ItemCode)
        .join(ItemCode, ItemCode.item_code_id == ItemTrade.item_code_id, isouter=True)
        .where(*filters)
        .order_by(ItemTrade.created_at.desc(), ItemTrade.item_trade_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    total_count = db.scalar(select(func.count()).select_from(ItemTrade).where(*filters)) or 0
    return ItemTradeListResponse(
        items=[to_item_trade_read(trade, code) for trade, code in rows],
        summaries=list_item_code_summaries(db, current_user=current_user),
        page=page,
        size=size,
        totalCount=total_count,
    )


def list_item_code_summaries(db: Session, *, current_user: User) -> list[ItemCodeSummary]:
    codes = db.scalars(
        select(ItemCode)
        .join(ItemTrade, ItemTrade.item_code_id == ItemCode.item_code_id)
        .where(
            ItemTrade.user_id == current_user.user_id,
            ItemTrade.is_deleted.is_(False),
            ItemTrade.trade_status == ACTIVE,
            ItemCode.is_deleted.is_(False),
        )
        .group_by(ItemCode.item_code_id)
        .order_by(ItemCode.item_name.asc(), ItemCode.item_code_id.asc())
    ).all()
    summaries: list[ItemCodeSummary] = []
    for code in codes:
        latest = get_latest_trade_for_code(db, current_user=current_user, item_code_id=code.item_code_id)
        inventory_quantity = latest.inventory_quantity_after if latest else 0
        inventory_value = latest.inventory_value_after if latest else 0
        average_buy_unit_price = (
            ceil_divide(inventory_value, inventory_quantity)
            if inventory_quantity and inventory_value
            else 0
        )
        fee_rate = effective_inventory_fee_rate(latest.fee_rate if latest else None)
        total_profit_amount = db.scalar(
            select(func.coalesce(func.sum(ItemTrade.profit_amount), 0)).where(
                ItemTrade.user_id == current_user.user_id,
                ItemTrade.item_code_id == code.item_code_id,
                ItemTrade.trade_type == SELL,
                ItemTrade.trade_status == ACTIVE,
                ItemTrade.is_deleted.is_(False),
            )
        ) or 0
        summaries.append(
            ItemCodeSummary(
                itemCodeId=code.item_code_id,
                itemCode=code.item_code,
                itemName=code.item_name,
                inventoryQuantity=inventory_quantity or 0,
                inventoryValue=inventory_value or 0,
                averageBuyUnitPrice=average_buy_unit_price,
                minimumProfitableUnitPrice=(
                    calculate_minimum_profitable_unit_price(average_buy_unit_price, fee_rate)
                    if average_buy_unit_price
                    else 0
                ),
                totalProfitAmount=total_profit_amount,
            )
        )
    return summaries


def to_item_code_read(code: ItemCode) -> ItemCodeRead:
    return ItemCodeRead(
        itemCodeId=code.item_code_id,
        itemCode=code.item_code,
        itemName=code.item_name,
        memo=code.memo,
        isActive=code.is_active,
        createdAt=code.created_at,
    )


def to_item_trade_read(trade: ItemTrade, code: ItemCode | None = None) -> ItemTradeRead:
    trade_date = trade.sell_date if trade.trade_type == SELL and trade.sell_date else trade.buy_date
    unit_price = trade.sell_unit_price if trade.trade_type == SELL and trade.sell_unit_price else trade.buy_unit_price
    return ItemTradeRead(
        itemTradeId=trade.item_trade_id,
        itemCodeId=trade.item_code_id,
        itemCode=code.item_code if code else None,
        itemName=code.item_name if code else trade.item_name,
        tradeType=trade.trade_type,
        tradeStatus=trade.trade_status,
        tradeDate=trade_date,
        unitPrice=unit_price,
        quantity=trade.quantity,
        feeRate=trade.fee_rate,
        minimumProfitableUnitPrice=trade.minimum_profitable_unit_price,
        averageBuyUnitPrice=trade.average_buy_unit_price,
        inventoryQuantityAfter=trade.inventory_quantity_after,
        inventoryValueAfter=trade.inventory_value_after,
        buyDate=trade.buy_date,
        buyUnitPrice=trade.buy_unit_price,
        sellDate=trade.sell_date,
        sellUnitPrice=trade.sell_unit_price,
        totalBuyAmount=trade.total_buy_amount,
        totalSellAmount=trade.total_sell_amount,
        feeAmount=trade.fee_amount,
        netSellAmount=trade.net_sell_amount,
        profitAmount=trade.profit_amount,
        cancelledAt=trade.cancelled_at,
        cancelReason=trade.cancel_reason,
        memo=trade.memo,
        createdAt=trade.created_at,
    )

from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.auth import User
from app.models.fx import FxBuyLot
from app.schemas.fx import BuyLotListResponse, BuyLotRead

OPEN = "open"
NUMERIC_SCALE = Decimal("0.000001")


def quantize_numeric(value: Decimal) -> Decimal:
    return value.quantize(NUMERIC_SCALE, rounding=ROUND_HALF_UP)


def calculate_usd_amount(buy_krw_amount: int, buy_exchange_rate: Decimal) -> Decimal:
    return quantize_numeric(Decimal(buy_krw_amount) / buy_exchange_rate)


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
    buy_lots = db.scalars(
        query.order_by(FxBuyLot.created_at.desc(), FxBuyLot.buy_lot_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

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

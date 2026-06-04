from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.fx import BuyLotCreateRequest, BuyLotListResponse, BuyLotRead
from app.services.fx import create_buy_lot, get_buy_lot, list_buy_lots

router = APIRouter(prefix="/fx", tags=["fx"])


@router.post(
    "/buy-lots",
    response_model=BuyLotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_buy_lot_route(
    payload: BuyLotCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BuyLotRead:
    buy_lot = create_buy_lot(
        db,
        current_user=current_user,
        buy_date=payload.buyDate,
        buy_krw_amount=payload.buyKrwAmount,
        buy_exchange_rate=payload.buyExchangeRate,
    )
    db.commit()
    return buy_lot


@router.get("/buy-lots", response_model=BuyLotListResponse)
def list_buy_lots_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    lot_status: str | None = None,
    is_active: bool | None = None,
) -> BuyLotListResponse:
    return list_buy_lots(
        db,
        current_user=current_user,
        page=page,
        size=size,
        lot_status=lot_status,
        is_active=is_active,
    )


@router.get("/buy-lots/{buy_lot_id}", response_model=BuyLotRead)
def get_buy_lot_route(
    buy_lot_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BuyLotRead:
    buy_lot = get_buy_lot(db, current_user=current_user, buy_lot_id=buy_lot_id)
    if buy_lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buy lot not found")

    return buy_lot

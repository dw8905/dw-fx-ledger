from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.item_trades import (
    ItemCodeListResponse,
    ItemTradeCancelRequest,
    ItemTradeCreateRequest,
    ItemTradeListResponse,
    ItemTradeRead,
)
from app.services.item_trades import cancel_item_trade, create_item_trade, list_item_codes, list_item_trades

router = APIRouter(prefix="/item-trades", tags=["item-trades"])


@router.get("/item-codes", response_model=ItemCodeListResponse)
def list_item_codes_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemCodeListResponse:
    _ = current_user
    return list_item_codes(db)


@router.get("", response_model=ItemTradeListResponse)
def list_item_trades_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ItemTradeListResponse:
    return list_item_trades(db, current_user=current_user, page=page, size=size)


@router.post("", response_model=ItemTradeRead, status_code=status.HTTP_201_CREATED)
def create_item_trade_route(
    payload: ItemTradeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemTradeRead:
    try:
        trade = create_item_trade(
            db,
            current_user=current_user,
            item_code=payload.itemCode,
            item_name=payload.itemName,
            trade_type=payload.tradeType,
            trade_date=payload.tradeDate,
            unit_price=payload.unitPrice,
            quantity=payload.quantity,
            fee_rate=payload.feeRate,
            memo=payload.memo,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    db.commit()
    return trade


@router.post("/{item_trade_id}/cancel", response_model=ItemTradeRead)
def cancel_item_trade_route(
    item_trade_id: int,
    payload: ItemTradeCancelRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemTradeRead:
    try:
        trade = cancel_item_trade(
            db,
            current_user=current_user,
            item_trade_id=item_trade_id,
            cancel_reason=payload.cancelReason,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    if trade is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item trade not found")

    db.commit()
    return trade

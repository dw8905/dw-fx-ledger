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
    """거래 입력 자동완성에 필요한 활성 자산 마스터 목록을 반환합니다."""

    _ = current_user
    return list_item_codes(db)


@router.get("", response_model=ItemTradeListResponse)
def list_item_trades_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
) -> ItemTradeListResponse:
    """현재 사용자의 자산 거래 목록과 재고 요약을 페이지 단위로 반환합니다."""

    return list_item_trades(db, current_user=current_user, page=page, size=size)


@router.post("", response_model=ItemTradeRead, status_code=status.HTTP_201_CREATED)
def create_item_trade_route(
    payload: ItemTradeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ItemTradeRead:
    """자산 매수/매도/재고조정 등록 요청을 처리하고 검증 오류를 400으로 변환합니다."""

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
    """자산 거래를 취소 처리하고 재고 재계산 충돌을 409로 변환합니다."""

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset trade not found")

    db.commit()
    return trade

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.fx import (
    BuyLotCreateRequest,
    BuyLotListResponse,
    BuyLotRead,
    BuyLotUpdateRequest,
    LotEventListResponse,
    SellTransactionCancelRequest,
    SellTransactionCreateRequest,
    SellTransactionListResponse,
    SellTransactionRead,
)
from app.services.fx import (
    InsufficientBuyLotBalanceError,
    cancel_sell_transaction,
    create_buy_lot,
    create_sell_transaction,
    get_buy_lot,
    get_sell_transaction,
    list_buy_lots,
    list_lot_events,
    list_sell_transactions,
    update_buy_lot,
)

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
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> BuyLotListResponse:
    try:
        return list_buy_lots(
            db,
            current_user=current_user,
            page=page,
            size=size,
            lot_status=lot_status,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


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


@router.put("/buy-lots/{buy_lot_id}", response_model=BuyLotRead)
def update_buy_lot_route(
    buy_lot_id: int,
    payload: BuyLotUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> BuyLotRead:
    try:
        buy_lot = update_buy_lot(
            db,
            current_user=current_user,
            buy_lot_id=buy_lot_id,
            buy_date=payload.buyDate,
            buy_krw_amount=payload.buyKrwAmount,
            buy_exchange_rate=payload.buyExchangeRate,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    if buy_lot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buy lot not found")

    db.commit()
    return buy_lot


@router.post(
    "/sell-transactions",
    response_model=SellTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_sell_transaction_route(
    payload: SellTransactionCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellTransactionRead:
    try:
        transaction = create_sell_transaction(
            db,
            current_user=current_user,
            sell_date=payload.sellDate,
            sell_usd_amount=payload.sellUsdAmount,
            sell_exchange_rate=payload.sellExchangeRate,
            allocation_strategy=payload.allocationStrategy
            or current_user.default_allocation_strategy,
            memo=payload.memo,
        )
    except InsufficientBuyLotBalanceError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    db.commit()
    return transaction


@router.post("/sell-transactions/{sell_transaction_id}/cancel", response_model=SellTransactionRead)
def cancel_sell_transaction_route(
    sell_transaction_id: int,
    payload: SellTransactionCancelRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellTransactionRead:
    try:
        transaction = cancel_sell_transaction(
            db,
            current_user=current_user,
            sell_transaction_id=sell_transaction_id,
            cancel_reason=payload.cancelReason,
        )
    except ValueError as error:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sell transaction not found",
        )

    db.commit()
    return transaction


@router.get("/lot-events", response_model=LotEventListResponse)
def list_lot_events_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
    root_buy_lot_id: int | None = None,
    sell_transaction_id: int | None = None,
) -> LotEventListResponse:
    return list_lot_events(
        db,
        current_user=current_user,
        page=page,
        size=size,
        root_buy_lot_id=root_buy_lot_id,
        sell_transaction_id=sell_transaction_id,
    )


@router.get("/sell-transactions", response_model=SellTransactionListResponse)
def list_sell_transactions_route(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: str | None = None,
    sort_order: str | None = None,
) -> SellTransactionListResponse:
    try:
        return list_sell_transactions(
            db,
            current_user=current_user,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error


@router.get("/sell-transactions/{sell_transaction_id}", response_model=SellTransactionRead)
def get_sell_transaction_route(
    sell_transaction_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SellTransactionRead:
    transaction = get_sell_transaction(
        db,
        current_user=current_user,
        sell_transaction_id=sell_transaction_id,
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sell transaction not found",
        )

    return transaction

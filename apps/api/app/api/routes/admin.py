from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.auth import User
from app.schemas.admin import (
    AdminItemCodeCreateRequest,
    AdminItemCodeListResponse,
    AdminItemCodeRead,
    AdminItemCodeUpdateRequest,
    AdminLotEventListResponse,
    AdminPostListResponse,
    AdminUserDetail,
    AdminUserLedgerResponse,
    AdminUserListResponse,
)
from app.schemas.fx import LedgerResponse
from app.services.admin import (
    create_admin_item_code,
    deactivate_admin_item_code,
    get_admin_user,
    get_admin_item_code,
    get_admin_user_detail,
    list_admin_item_codes,
    list_admin_lot_events,
    list_admin_posts,
    list_admin_users,
    to_admin_user_list_item,
    update_admin_item_code,
)
from app.services.fx import list_ledger

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def admin_health(current_user: Annotated[User, Depends(require_admin)]) -> dict[str, int | str]:
    return {"status": "ok", "userId": current_user.user_id}


@router.get("/users", response_model=AdminUserListResponse)
def list_users_route(
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    keyword: str | None = None,
    user_status: str | None = None,
    role: str | None = None,
) -> AdminUserListResponse:
    return list_admin_users(
        db,
        page=page,
        size=size,
        keyword=keyword,
        user_status=user_status,
        role=role,
    )


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_user_route(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
) -> AdminUserDetail:
    user = get_admin_user_detail(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.get("/posts", response_model=AdminPostListResponse)
def list_posts_route(
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    include_deleted: bool = False,
    post_status: str | None = None,
    keyword: str | None = None,
) -> AdminPostListResponse:
    return list_admin_posts(
        db,
        page=page,
        size=size,
        include_deleted=include_deleted,
        post_status=post_status,
        keyword=keyword,
    )


@router.get("/fx/users/{user_id}/ledger", response_model=AdminUserLedgerResponse)
def get_user_ledger_route(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
    period: str = "all",
) -> AdminUserLedgerResponse:
    user = get_admin_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        ledger: LedgerResponse = list_ledger(db, current_user=user, period=period)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

    return AdminUserLedgerResponse(user=to_admin_user_list_item(user), ledger=ledger)


@router.get("/fx/lot-events", response_model=AdminLotEventListResponse)
def list_lot_events_route(
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    user_id: int | None = None,
    event_type: str | None = None,
    sell_transaction_id: int | None = None,
    root_buy_lot_id: int | None = None,
) -> AdminLotEventListResponse:
    return list_admin_lot_events(
        db,
        page=page,
        size=size,
        user_id=user_id,
        event_type=event_type,
        sell_transaction_id=sell_transaction_id,
        root_buy_lot_id=root_buy_lot_id,
    )


@router.get("/item-codes", response_model=AdminItemCodeListResponse)
def list_item_codes_route(
    db: Annotated[Session, Depends(get_db)],
    _admin_user: Annotated[User, Depends(require_admin)],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
) -> AdminItemCodeListResponse:
    return list_admin_item_codes(
        db,
        page=page,
        size=size,
        keyword=keyword,
        is_active=is_active,
    )


@router.post("/item-codes", response_model=AdminItemCodeRead, status_code=status.HTTP_201_CREATED)
def create_item_code_route(
    payload: AdminItemCodeCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> AdminItemCodeRead:
    try:
        code = create_admin_item_code(
            db,
            admin_user=admin_user,
            item_name=payload.item_name,
            memo=payload.memo,
            is_active=payload.is_active,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    db.commit()
    return code


@router.put("/item-codes/{item_code_id}", response_model=AdminItemCodeRead)
def update_item_code_route(
    item_code_id: int,
    payload: AdminItemCodeUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> AdminItemCodeRead:
    code = get_admin_item_code(db, item_code_id=item_code_id)
    if code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item code not found")

    try:
        updated = update_admin_item_code(
            db,
            admin_user=admin_user,
            code=code,
            item_name=payload.item_name,
            memo=payload.memo,
            is_active=payload.is_active,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error

    db.commit()
    return updated


@router.delete("/item-codes/{item_code_id}", response_model=AdminItemCodeRead)
def deactivate_item_code_route(
    item_code_id: int,
    db: Annotated[Session, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin)],
) -> AdminItemCodeRead:
    code = get_admin_item_code(db, item_code_id=item_code_id)
    if code is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item code not found")

    deactivated = deactivate_admin_item_code(db, admin_user=admin_user, code=code)
    db.commit()
    return deactivated

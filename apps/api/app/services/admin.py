from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import User, UserRole
from app.models.board import BoardPost
from app.models.fx import FxBuyLot, FxLotEvent, FxSellTransaction
from app.schemas.admin import (
    AdminFxSummary,
    AdminLotEventListResponse,
    AdminLotEventRead,
    AdminPostListItem,
    AdminPostListResponse,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
)
from app.services.fx import COMPLETED, OPEN


def _role_codes(user: User) -> list[str]:
    return sorted(user_role.role.role_code for user_role in user.roles if user_role.role)


def to_admin_user_list_item(user: User) -> AdminUserListItem:
    return AdminUserListItem(
        user_id=user.user_id,
        email=user.email,
        login_id=user.login_id,
        display_name=user.display_name,
        user_status=user.user_status,
        roles=_role_codes(user),
        created_at=user.created_at,
    )


def list_admin_users(db: Session, *, page: int, size: int) -> AdminUserListResponse:
    total_count = db.scalar(select(func.count()).select_from(User).where(User.is_deleted.is_(False)))
    users = db.scalars(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.is_deleted.is_(False))
        .order_by(User.created_at.desc(), User.user_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return AdminUserListResponse(
        items=[to_admin_user_list_item(user) for user in users],
        page=page,
        size=size,
        total_count=total_count or 0,
    )


def get_admin_user(db: Session, *, user_id: int) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.user_id == user_id, User.is_deleted.is_(False))
    )


def get_admin_user_detail(db: Session, *, user_id: int) -> AdminUserDetail | None:
    user = get_admin_user(db, user_id=user_id)
    if user is None:
        return None

    total_real_profit = db.scalar(
        select(func.coalesce(func.sum(FxSellTransaction.total_real_profit_krw), 0)).where(
            FxSellTransaction.user_id == user.user_id,
            FxSellTransaction.transaction_status == COMPLETED,
            FxSellTransaction.is_deleted.is_(False),
        )
    ) or 0
    total_display_profit = db.scalar(
        select(func.coalesce(func.sum(FxSellTransaction.total_display_profit_krw), 0)).where(
            FxSellTransaction.user_id == user.user_id,
            FxSellTransaction.transaction_status == COMPLETED,
            FxSellTransaction.is_deleted.is_(False),
        )
    ) or 0
    open_usd_amount = db.scalar(
        select(func.coalesce(func.sum(FxBuyLot.usd_amount), Decimal("0"))).where(
            FxBuyLot.user_id == user.user_id,
            FxBuyLot.lot_status == OPEN,
            FxBuyLot.is_active.is_(True),
            FxBuyLot.is_deleted.is_(False),
        )
    ) or Decimal("0")

    return AdminUserDetail(
        **to_admin_user_list_item(user).model_dump(),
        default_allocation_strategy=user.default_allocation_strategy,
        updated_at=user.updated_at,
        fx_summary=AdminFxSummary(
            buy_lot_count=db.scalar(
                select(func.count()).select_from(FxBuyLot).where(FxBuyLot.user_id == user.user_id)
            )
            or 0,
            open_lot_count=db.scalar(
                select(func.count()).select_from(FxBuyLot).where(
                    FxBuyLot.user_id == user.user_id,
                    FxBuyLot.lot_status == OPEN,
                    FxBuyLot.is_active.is_(True),
                    FxBuyLot.is_deleted.is_(False),
                )
            )
            or 0,
            sell_transaction_count=db.scalar(
                select(func.count()).select_from(FxSellTransaction).where(
                    FxSellTransaction.user_id == user.user_id
                )
            )
            or 0,
            lot_event_count=db.scalar(
                select(func.count()).select_from(FxLotEvent).where(FxLotEvent.user_id == user.user_id)
            )
            or 0,
            total_real_profit_krw=total_real_profit,
            total_display_profit_krw=total_display_profit,
            open_usd_amount=open_usd_amount,
        ),
    )


def list_admin_posts(
    db: Session,
    *,
    page: int,
    size: int,
    include_deleted: bool,
    post_status: str | None,
) -> AdminPostListResponse:
    filters = []
    if not include_deleted:
        filters.append(BoardPost.is_deleted.is_(False))
    if post_status is not None:
        filters.append(BoardPost.post_status == post_status)

    count_query = select(func.count()).select_from(BoardPost).where(*filters)
    rows = db.execute(
        select(BoardPost, User.display_name)
        .join(User, User.user_id == BoardPost.author_id)
        .where(*filters)
        .order_by(BoardPost.created_at.desc(), BoardPost.post_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return AdminPostListResponse(
        items=[
            AdminPostListItem(
                post_id=post.post_id,
                author_id=post.author_id,
                author_name=author_name,
                title=post.title,
                view_count=post.view_count,
                post_status=post.post_status,
                is_deleted=post.is_deleted,
                created_at=post.created_at,
                updated_at=post.updated_at,
            )
            for post, author_name in rows
        ],
        page=page,
        size=size,
        total_count=db.scalar(count_query) or 0,
    )


def list_admin_lot_events(
    db: Session,
    *,
    page: int,
    size: int,
    user_id: int | None,
    event_type: str | None,
) -> AdminLotEventListResponse:
    filters = []
    if user_id is not None:
        filters.append(FxLotEvent.user_id == user_id)
    if event_type is not None:
        filters.append(FxLotEvent.event_type == event_type)

    count_query = select(func.count()).select_from(FxLotEvent).where(*filters)
    events = db.scalars(
        select(FxLotEvent)
        .where(*filters)
        .order_by(FxLotEvent.created_at.desc(), FxLotEvent.lot_event_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()

    return AdminLotEventListResponse(
        items=[
            AdminLotEventRead(
                lot_event_id=event.lot_event_id,
                user_id=event.user_id,
                event_type=event.event_type,
                event_status=event.event_status,
                root_buy_lot_id=event.root_buy_lot_id,
                sell_transaction_id=event.sell_transaction_id,
                lot_allocation_id=event.lot_allocation_id,
                source_buy_lot_id=event.source_buy_lot_id,
                closed_buy_lot_id=event.closed_buy_lot_id,
                remaining_buy_lot_id=event.remaining_buy_lot_id,
                restored_buy_lot_id=event.restored_buy_lot_id,
                related_event_id=event.related_event_id,
                event_payload=event.event_payload,
                created_at=event.created_at,
            )
            for event in events
        ],
        page=page,
        size=size,
        total_count=db.scalar(count_query) or 0,
    )

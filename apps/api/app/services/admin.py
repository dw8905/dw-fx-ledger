from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import User, UserRole
from app.models.board import BoardPost
from app.models.fx import FxBuyLot, FxLotEvent, FxSellTransaction
from app.models.item_trade import ItemCode
from app.schemas.admin import (
    AdminFxSummary,
    AdminItemCodeListResponse,
    AdminItemCodeRead,
    AdminLotEventListResponse,
    AdminLotEventRead,
    AdminPostListItem,
    AdminPostListResponse,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
)
from app.services.fx import COMPLETED, OPEN, list_ledger


def total_pages(total_count: int, size: int) -> int:
    """총 건수와 페이지 크기로 UI에 표시할 전체 페이지 수를 계산합니다."""

    if total_count == 0:
        return 0

    return (total_count + size - 1) // size


def _role_codes(user: User) -> list[str]:
    """UserRole 관계에서 role_code만 꺼내 정렬된 문자열 목록으로 만듭니다."""

    return sorted(user_role.role.role_code for user_role in user.roles if user_role.role)


def to_admin_user_list_item(user: User) -> AdminUserListItem:
    """User 모델을 관리자 사용자 목록 행 스키마로 변환합니다."""

    return AdminUserListItem(
        user_id=user.user_id,
        email=user.email,
        login_id=user.login_id,
        display_name=user.display_name,
        user_status=user.user_status,
        roles=_role_codes(user),
        created_at=user.created_at,
    )


def list_admin_users(
    db: Session,
    *,
    page: int,
    size: int,
    keyword: str | None,
    user_status: str | None,
    role: str | None,
) -> AdminUserListResponse:
    """관리자 사용자 목록에 검색어, 상태, role 필터와 페이지네이션을 적용합니다."""

    filters = [User.is_deleted.is_(False)]
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(
            or_(
                User.email.ilike(pattern),
                User.login_id.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )
    if user_status:
        filters.append(User.user_status == user_status)
    if role:
        filters.append(User.roles.any(UserRole.role.has(role_code=role)))

    total_count = db.scalar(select(func.count()).select_from(User).where(*filters)) or 0
    users = db.scalars(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(*filters)
        .order_by(User.created_at.desc(), User.user_id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return AdminUserListResponse(
        items=[to_admin_user_list_item(user) for user in users],
        page=page,
        size=size,
        total_count=total_count,
        total_pages=total_pages(total_count, size),
    )


def get_admin_user(db: Session, *, user_id: int) -> User | None:
    """관리자 상세/원장 조회에서 사용할 사용자와 role 관계를 로드합니다."""

    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.user_id == user_id, User.is_deleted.is_(False))
    )


def get_admin_user_detail(db: Session, *, user_id: int) -> AdminUserDetail | None:
    """사용자 기본 정보와 FX 요약을 합쳐 관리자 상세 응답을 구성합니다."""

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
    total_buy_krw_amount = db.scalar(
        select(func.coalesce(func.sum(FxBuyLot.buy_krw_amount), 0)).where(
            FxBuyLot.user_id == user.user_id,
            FxBuyLot.is_deleted.is_(False),
        )
    ) or 0
    total_buy_usd_amount = db.scalar(
        select(func.coalesce(func.sum(FxBuyLot.usd_amount), Decimal("0"))).where(
            FxBuyLot.user_id == user.user_id,
            FxBuyLot.is_deleted.is_(False),
        )
    ) or Decimal("0")
    ledger_summary = list_ledger(db, current_user=user, period="all", currency_code="USD").summary

    return AdminUserDetail(
        **to_admin_user_list_item(user).model_dump(),
        default_allocation_strategy=user.default_allocation_strategy,
        updated_at=user.updated_at,
        fx_summary=AdminFxSummary(
            total_buy_krw_amount=total_buy_krw_amount,
            total_buy_usd_amount=total_buy_usd_amount,
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
            final_cumulative_profit_krw=ledger_summary.finalCumulativeProfitKrw,
            latest_ledger_date=(
                ledger_summary.latestLedgerDate.isoformat()
                if ledger_summary.latestLedgerDate is not None
                else None
            ),
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
    keyword: str | None,
) -> AdminPostListResponse:
    """관리자 게시글 목록에서 삭제글 포함 여부, 상태, 검색어를 적용합니다."""

    filters = []
    if not include_deleted:
        filters.append(BoardPost.is_deleted.is_(False))
    if post_status is not None:
        filters.append(BoardPost.post_status == post_status)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(
            or_(
                BoardPost.title.ilike(pattern),
                BoardPost.content.ilike(pattern),
                User.email.ilike(pattern),
                User.login_id.ilike(pattern),
                User.display_name.ilike(pattern),
            )
        )

    count_query = (
        select(func.count())
        .select_from(BoardPost)
        .join(User, User.user_id == BoardPost.author_id)
        .where(*filters)
    )
    total_count = db.scalar(count_query) or 0
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
        total_count=total_count,
        total_pages=total_pages(total_count, size),
    )


def list_admin_lot_events(
    db: Session,
    *,
    page: int,
    size: int,
    user_id: int | None,
    event_type: str | None,
    sell_transaction_id: int | None,
    root_buy_lot_id: int | None,
) -> AdminLotEventListResponse:
    """관리자 FX 이벤트 로그에 사용자/이벤트/거래/루트 로트 필터를 적용합니다."""

    filters = []
    if user_id is not None:
        filters.append(FxLotEvent.user_id == user_id)
    if event_type is not None:
        filters.append(FxLotEvent.event_type == event_type)
    if sell_transaction_id is not None:
        filters.append(FxLotEvent.sell_transaction_id == sell_transaction_id)
    if root_buy_lot_id is not None:
        filters.append(FxLotEvent.root_buy_lot_id == root_buy_lot_id)

    total_count = db.scalar(select(func.count()).select_from(FxLotEvent).where(*filters)) or 0
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
        total_count=total_count,
        total_pages=total_pages(total_count, size),
    )


def list_admin_item_codes(
    db: Session,
    *,
    page: int,
    size: int,
    keyword: str | None,
    is_active: bool | None,
) -> AdminItemCodeListResponse:
    """관리자 자산 마스터 목록에 검색어와 활성 상태 필터를 적용합니다."""

    filters = [ItemCode.is_deleted.is_(False)]
    if keyword:
        pattern = f"%{keyword.strip()}%"
        filters.append(or_(ItemCode.item_code.ilike(pattern), ItemCode.item_name.ilike(pattern)))
    if is_active is not None:
        filters.append(ItemCode.is_active.is_(is_active))

    total_count = db.scalar(select(func.count()).select_from(ItemCode).where(*filters)) or 0
    rows = db.scalars(
        select(ItemCode)
        .where(*filters)
        .order_by(ItemCode.item_name.asc(), ItemCode.item_code_id.asc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return AdminItemCodeListResponse(
        items=[to_admin_item_code_read(row) for row in rows],
        page=page,
        size=size,
        total_count=total_count,
        total_pages=total_pages(total_count, size),
    )


def get_admin_item_code(db: Session, *, item_code_id: int) -> ItemCode | None:
    """수정/비활성화 대상 자산 마스터를 ID로 조회합니다."""

    return db.scalar(
        select(ItemCode).where(
            ItemCode.item_code_id == item_code_id,
            ItemCode.is_deleted.is_(False),
        )
    )


def item_code_exists(db: Session, *, item_code: str, exclude_item_code_id: int | None = None) -> bool:
    """자산 코드가 이미 사용 중인지 확인해 중복 등록을 막습니다."""

    filters = [ItemCode.item_code == item_code.strip(), ItemCode.is_deleted.is_(False)]
    if exclude_item_code_id is not None:
        filters.append(ItemCode.item_code_id != exclude_item_code_id)
    return (db.scalar(select(func.count()).select_from(ItemCode).where(*filters)) or 0) > 0


def item_name_exists(db: Session, *, item_name: str, exclude_item_code_id: int | None = None) -> bool:
    """자산명을 대소문자 무시 방식으로 비교해 같은 이름의 중복 등록을 막습니다."""

    normalized_name = item_name.strip()
    filters = [
        func.lower(ItemCode.item_name) == normalized_name.lower(),
        ItemCode.is_deleted.is_(False),
    ]
    if exclude_item_code_id is not None:
        filters.append(ItemCode.item_code_id != exclude_item_code_id)
    return (db.scalar(select(func.count()).select_from(ItemCode).where(*filters)) or 0) > 0


def create_admin_item_code(
    db: Session,
    *,
    admin_user: User,
    item_name: str,
    memo: str | None,
    is_active: bool,
) -> AdminItemCodeRead:
    """관리자가 자산명을 등록하면 내부 코드 ITEM-000001 형태를 자동 생성합니다."""

    if item_name_exists(db, item_name=item_name):
        raise ValueError("Asset name already exists")

    code = ItemCode(
        user_id=None,
        item_code=f"PENDING-{uuid4().hex}",
        item_name=item_name.strip(),
        memo=memo,
        is_active=is_active,
        created_by=admin_user.user_id,
        updated_by=admin_user.user_id,
    )
    db.add(code)
    db.flush()
    code.item_code = f"ITEM-{code.item_code_id:06d}"
    db.flush()
    db.refresh(code)
    return to_admin_item_code_read(code)


def update_admin_item_code(
    db: Session,
    *,
    admin_user: User,
    code: ItemCode,
    item_name: str,
    memo: str | None,
    is_active: bool,
) -> AdminItemCodeRead:
    """기존 자산 마스터의 이름, 메모, 활성 상태를 수정합니다."""

    if item_name_exists(db, item_name=item_name, exclude_item_code_id=code.item_code_id):
        raise ValueError("Asset name already exists")

    code.item_name = item_name.strip()
    code.memo = memo
    code.is_active = is_active
    code.updated_by = admin_user.user_id
    db.flush()
    db.refresh(code)
    return to_admin_item_code_read(code)


def deactivate_admin_item_code(
    db: Session,
    *,
    admin_user: User,
    code: ItemCode,
) -> AdminItemCodeRead:
    """자산 마스터를 삭제하지 않고 비활성 처리해 기존 거래 참조를 보존합니다."""

    code.is_active = False
    code.updated_by = admin_user.user_id
    db.flush()
    db.refresh(code)
    return to_admin_item_code_read(code)


def to_admin_item_code_read(code: ItemCode) -> AdminItemCodeRead:
    """ItemCode ORM 모델을 관리자 응답 스키마로 변환합니다."""

    return AdminItemCodeRead(
        item_code_id=code.item_code_id,
        item_code=code.item_code,
        item_name=code.item_name,
        memo=code.memo,
        is_active=code.is_active,
        is_deleted=code.is_deleted,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )

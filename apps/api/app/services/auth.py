from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import RefreshToken, User, UserRole
from app.schemas.auth import UserRead
from app.services.roles import USER_ROLE_CODE, USER_ROLE_NAME, ensure_role
from app.services.security import create_access_token, create_refresh_token, hash_password, hash_token


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    display_name: str,
    login_id: str | None,
    default_allocation_strategy: str,
) -> User:
    role = ensure_role(db, role_code=USER_ROLE_CODE, role_name=USER_ROLE_NAME)
    user = User(
        email=email,
        login_id=login_id,
        password_hash=hash_password(password),
        display_name=display_name,
        default_allocation_strategy=default_allocation_strategy,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.user_id, role_id=role.role_id))
    db.flush()
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.email == email, User.is_deleted.is_(False))
    )


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(
            (User.email == identifier) | (User.login_id == identifier),
            User.is_deleted.is_(False),
        )
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.roles).selectinload(UserRole.role))
        .where(User.user_id == user_id, User.is_deleted.is_(False))
    )


def issue_token_pair(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.user_id)
    refresh_token, expires_at = create_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.user_id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
        )
    )
    db.flush()
    return access_token, refresh_token


def revoke_refresh_token(db: Session, refresh_token: str) -> bool:
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.revoked_at.is_(None),
        )
    )
    if token is None:
        return False

    token.revoked_at = datetime.now(UTC)
    db.flush()
    return True


def consume_refresh_token(db: Session, refresh_token: str) -> User | None:
    token = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    if token is None:
        return None

    user = get_user_by_id(db, token.user_id)
    if user is None or user.user_status != "active":
        return None

    token.revoked_at = datetime.now(UTC)
    db.flush()
    return user


def to_user_read(user: User) -> UserRead:
    roles = [user_role.role.role_code for user_role in user.roles if user_role.role is not None]
    return UserRead(
        user_id=user.user_id,
        email=user.email,
        login_id=user.login_id,
        display_name=user.display_name,
        user_status=user.user_status,
        default_allocation_strategy=user.default_allocation_strategy,
        roles=roles,
    )

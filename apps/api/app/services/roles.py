from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.auth import Role, User, UserRole

USER_ROLE_CODE = "user"
USER_ROLE_NAME = "User"
ADMIN_ROLE_CODE = "admin"
ADMIN_ROLE_NAME = "Admin"


def get_role_by_code(db: Session, role_code: str) -> Role | None:
    return db.scalar(select(Role).where(Role.role_code == role_code))


def ensure_role(
    db: Session,
    *,
    role_code: str,
    role_name: str,
    description: str | None = None,
) -> Role:
    role = get_role_by_code(db, role_code)
    if role is not None:
        return role

    role = Role(role_code=role_code, role_name=role_name, description=description)
    db.add(role)
    db.flush()
    return role


def ensure_base_roles(db: Session) -> list[Role]:
    return [
        ensure_role(
            db,
            role_code=USER_ROLE_CODE,
            role_name=USER_ROLE_NAME,
            description="Default application user",
        ),
        ensure_role(
            db,
            role_code=ADMIN_ROLE_CODE,
            role_name=ADMIN_ROLE_NAME,
            description="Application administrator",
        ),
    ]


def ensure_user_role(
    db: Session,
    *,
    user: User,
    role_code: str,
    created_by: int | None = None,
) -> UserRole:
    role = ensure_role(
        db,
        role_code=role_code,
        role_name=ADMIN_ROLE_NAME if role_code == ADMIN_ROLE_CODE else role_code.title(),
    )
    user_role = db.scalar(
        select(UserRole).where(UserRole.user_id == user.user_id, UserRole.role_id == role.role_id)
    )
    if user_role is not None:
        return user_role

    user_role = UserRole(user_id=user.user_id, role_id=role.role_id, created_by=created_by)
    db.add(user_role)
    db.flush()
    return user_role


def grant_admin_role(db: Session, *, user: User, created_by: int | None = None) -> UserRole:
    return ensure_user_role(db, user=user, role_code=ADMIN_ROLE_CODE, created_by=created_by)


def user_has_role(user: User, role_code: str) -> bool:
    return any(user_role.role and user_role.role.role_code == role_code for user_role in user.roles)


def user_role_count(db: Session, *, user: User, role_code: str) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(UserRole)
            .join(Role, Role.role_id == UserRole.role_id)
            .where(UserRole.user_id == user.user_id, Role.role_code == role_code)
        )
        or 0
    )

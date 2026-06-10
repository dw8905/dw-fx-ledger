from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.auth import User
from app.services.auth import get_user_by_id
from app.services.roles import ADMIN_ROLE_CODE, user_has_role
from app.services.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
    access_cookie: Annotated[
        str | None, Cookie(alias=settings.access_token_cookie_name)
    ] = None,
) -> User:
    """Bearer 헤더 또는 HttpOnly 쿠키에서 access token을 읽어 현재 사용자를 찾습니다."""

    token = credentials.credentials if credentials is not None else access_cookie
    user_id = decode_access_token(token) if token is not None else None
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if user is None or user.user_status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """현재 사용자가 admin role을 갖고 있는지 확인하고 없으면 403을 발생시킵니다."""

    if not user_has_role(current_user, ADMIN_ROLE_CODE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return current_user

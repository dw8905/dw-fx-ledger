from typing import Annotated

from fastapi import APIRouter, Body, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.auth import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    UserRead,
)
from app.services.cookies import clear_auth_cookies, set_auth_cookies
from app.services.auth import (
    consume_refresh_token,
    create_user,
    get_user_by_email,
    get_user_by_identifier,
    issue_token_pair,
    revoke_refresh_token,
    to_user_read,
)
from app.services.security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.email == payload.email,
                User.login_id == payload.login_id if payload.login_id is not None else False,
            )
        )
    )
    if existing_user is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

    user = create_user(
        db,
        email=str(payload.email),
        password=payload.password,
        display_name=payload.display_name,
        login_id=payload.login_id,
        default_allocation_strategy=payload.default_allocation_strategy,
    )
    access_token, refresh_token = issue_token_pair(db, user)
    db.commit()
    db.refresh(user)
    user = get_user_by_email(db, str(payload.email)) or user
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return AuthResponse(user=to_user_read(user))


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AuthResponse:
    user = get_user_by_identifier(db, payload.identifier)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if user.user_status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    access_token, refresh_token = issue_token_pair(db, user)
    db.commit()
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return AuthResponse(user=to_user_read(user))


@router.post("/refresh", response_model=MessageResponse)
def refresh(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[RefreshRequest | None, Body()] = None,
    refresh_cookie: Annotated[
        str | None, Cookie(alias=settings.refresh_token_cookie_name)
    ] = None,
) -> MessageResponse:
    refresh_token_value = payload.refresh_token if payload and payload.refresh_token else refresh_cookie
    if refresh_token_value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    user = consume_refresh_token(db, refresh_token_value)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token, refresh_token = issue_token_pair(db, user)
    db.commit()
    set_auth_cookies(response, access_token=access_token, refresh_token=refresh_token)
    return MessageResponse(message="Token refreshed")


@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[LogoutRequest | None, Body()] = None,
    refresh_cookie: Annotated[
        str | None, Cookie(alias=settings.refresh_token_cookie_name)
    ] = None,
) -> MessageResponse:
    refresh_token_value = payload.refresh_token if payload and payload.refresh_token else refresh_cookie
    if refresh_token_value is not None:
        revoke_refresh_token(db, refresh_token_value)
    db.commit()
    clear_auth_cookies(response)
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return to_user_read(current_user)

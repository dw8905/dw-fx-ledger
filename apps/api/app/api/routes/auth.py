from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.auth import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserRead,
)
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
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
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
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=to_user_read(user),
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> AuthResponse:
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
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=to_user_read(user),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> TokenPair:
    user = consume_refresh_token(db, payload.refresh_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    access_token, refresh_token = issue_token_pair(db, user)
    db.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: Annotated[Session, Depends(get_db)]) -> MessageResponse:
    revoke_refresh_token(db, payload.refresh_token)
    db.commit()
    return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return to_user_read(current_user)

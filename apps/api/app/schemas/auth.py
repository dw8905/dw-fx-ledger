from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    user_id: int
    email: EmailStr
    login_id: str | None
    display_name: str
    user_status: str
    default_allocation_strategy: str
    roles: list[str]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    login_id: str | None = Field(default=None, min_length=3, max_length=100)
    default_allocation_strategy: Literal["highest_rate_first", "fifo", "lifo"] = "highest_rate_first"


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, max_length=255)
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPair):
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    message: str

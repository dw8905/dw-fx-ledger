from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserRead(BaseModel):
    """프론트에서 현재 로그인 사용자 정보를 표시할 때 사용하는 응답 모델입니다."""

    user_id: int
    email: EmailStr
    login_id: str | None
    display_name: str
    user_status: str
    default_allocation_strategy: str
    roles: list[str]


class RegisterRequest(BaseModel):
    """회원가입 요청 바디이며 최소한의 계정 생성 입력값을 검증합니다."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    login_id: str | None = Field(default=None, min_length=3, max_length=100)
    default_allocation_strategy: Literal["highest_rate_first", "fifo", "lifo"] = "highest_rate_first"


class LoginRequest(BaseModel):
    """이메일 또는 로그인 ID와 비밀번호로 로그인할 때 받는 요청 모델입니다."""

    identifier: str = Field(min_length=1, max_length=255)
    password: str


class TokenPair(BaseModel):
    """API 내부에서 access/refresh 토큰 한 쌍을 표현할 때 쓰는 모델입니다."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """인증 성공 후 쿠키와 함께 내려주는 사용자 정보 응답입니다."""

    user: UserRead


class RefreshRequest(BaseModel):
    """레거시/테스트 호환을 위해 refresh token을 바디로도 받을 수 있는 모델입니다."""

    refresh_token: str | None = None


class LogoutRequest(BaseModel):
    """로그아웃 시 특정 refresh token 무효화를 요청할 수 있는 모델입니다."""

    refresh_token: str | None = None


class MessageResponse(BaseModel):
    """단순 성공/실패 메시지를 내려줄 때 사용하는 공통 응답 모델입니다."""

    message: str

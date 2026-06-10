from fastapi import Response

from app.core.config import settings


def set_auth_cookies(response: Response, *, access_token: str, refresh_token: str) -> None:
    """브라우저가 직접 읽지 못하도록 인증 토큰을 HttpOnly 쿠키로 내려줍니다."""

    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    """로그아웃 또는 토큰 폐기 시 브라우저에 저장된 인증 쿠키를 제거합니다."""

    for cookie_name in (
        settings.access_token_cookie_name,
        settings.refresh_token_cookie_name,
    ):
        response.delete_cookie(
            key=cookie_name,
            httponly=True,
            secure=settings.auth_cookie_secure,
            samesite=settings.auth_cookie_samesite,
            path="/",
        )

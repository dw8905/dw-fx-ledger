from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """평문 비밀번호를 DB에 저장하지 않도록 bcrypt 해시로 변환합니다."""

    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """로그인 시 입력 비밀번호가 저장된 bcrypt 해시와 일치하는지 확인합니다."""

    return pwd_context.verify(password, password_hash)


def hash_token(token: str) -> str:
    """리프레시 토큰 원문이 유출되지 않도록 SHA-256 해시만 DB에 저장합니다."""

    return sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int) -> str:
    """사용자 ID를 subject로 담은 짧은 수명의 JWT access token을 생성합니다."""

    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> tuple[str, datetime]:
    """재발급에 쓸 긴 랜덤 refresh token 원문과 만료 시각을 생성합니다."""

    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    return uuid4().hex + uuid4().hex, expires_at


def decode_access_token(token: str) -> int | None:
    """JWT access token을 검증하고 유효하면 subject의 사용자 ID를 반환합니다."""

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

    if payload.get("type") != "access":
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    try:
        return int(subject)
    except ValueError:
        return None

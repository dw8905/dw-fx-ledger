from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """환경변수와 .env 값을 FastAPI 설정 객체로 읽어오는 클래스입니다."""

    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"
    cors_origins: str = "http://localhost:3000,http://localhost:3001"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    access_token_cookie_name: str = "dw_fx_ledger_access_token"
    refresh_token_cookie_name: str = "dw_fx_ledger_refresh_token"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        """콤마로 저장된 CORS origin 문자열을 FastAPI가 쓰는 리스트로 변환합니다."""

        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

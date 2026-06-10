from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """FastAPI dependency에서 요청마다 DB 세션을 열고 응답 후 안전하게 닫습니다."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

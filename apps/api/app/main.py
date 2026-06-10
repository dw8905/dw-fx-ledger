from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.fx import router as fx_router
from app.api.routes.item_trades import router as item_trades_router
from app.api.routes.posts import router as posts_router
from app.core.config import settings

app = FastAPI(title="DW FX Ledger API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(fx_router)
app.include_router(item_trades_router)
app.include_router(posts_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    """로드밸런서나 개발자가 API 서버 생존 여부를 확인하는 단순 헬스체크입니다."""

    return {"status": "ok"}

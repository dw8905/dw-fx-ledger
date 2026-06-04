from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.fx import router as fx_router
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
app.include_router(posts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

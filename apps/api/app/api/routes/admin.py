from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.models.auth import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health")
def admin_health(current_user: Annotated[User, Depends(require_admin)]) -> dict[str, int | str]:
    return {"status": "ok", "userId": current_user.user_id}

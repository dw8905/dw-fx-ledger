from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.services.auth import get_user_by_identifier
from app.services.roles import ADMIN_ROLE_CODE, ensure_base_roles, grant_admin_role, user_role_count


def register_user(client: TestClient, suffix: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": f"admin-test-{suffix}@example.com",
            "login_id": f"admin_test_{suffix}",
            "password": "password123",
            "display_name": f"Admin Test User {suffix}",
            "default_allocation_strategy": "highest_rate_first",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


def test_admin_endpoint_requires_admin_role() -> None:
    user_client = TestClient(app)
    admin_client = TestClient(app)
    user_suffix = uuid4().hex[:12]
    admin_suffix = uuid4().hex[:12]

    register_user(user_client, user_suffix)
    admin = register_user(admin_client, admin_suffix)

    user_response = user_client.get("/admin/health")
    assert user_response.status_code == 403

    with SessionLocal() as db:
        ensure_base_roles(db)
        admin_user = get_user_by_identifier(db, admin["login_id"])
        assert admin_user is not None
        grant_admin_role(db, user=admin_user)
        db.commit()

    admin_response = admin_client.get("/admin/health")
    assert admin_response.status_code == 200, admin_response.text
    assert admin_response.json() == {"status": "ok", "userId": admin["user_id"]}


def test_grant_admin_role_is_idempotent() -> None:
    client = TestClient(app)
    suffix = uuid4().hex[:12]
    registered = register_user(client, suffix)

    with SessionLocal() as db:
        ensure_base_roles(db)
        user = get_user_by_identifier(db, registered["login_id"])
        assert user is not None

        grant_admin_role(db, user=user)
        grant_admin_role(db, user=user)
        db.commit()

        assert user_role_count(db, user=user, role_code=ADMIN_ROLE_CODE) == 1

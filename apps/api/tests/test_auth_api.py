from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_auth_flow() -> None:
    unique = uuid4().hex[:12]
    email = f"auth-{unique}@example.com"
    login_id = f"auth_{unique}"

    register_response = client.post(
        "/auth/register",
        json={
            "email": email,
            "login_id": login_id,
            "password": "password123",
            "display_name": "Auth Test User",
            "default_allocation_strategy": "highest_rate_first",
        },
    )
    assert register_response.status_code == 201, register_response.text
    register_body = register_response.json()
    assert register_body["access_token"]
    assert register_body["refresh_token"]
    assert register_body["user"]["email"] == email
    assert "user" in register_body["user"]["roles"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {register_body['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    assert me_response.json()["login_id"] == login_id

    login_response = client.post(
        "/auth/login",
        json={"identifier": login_id, "password": "password123"},
    )
    assert login_response.status_code == 200, login_response.text
    login_body = login_response.json()
    assert login_body["access_token"]
    assert login_body["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": login_body["refresh_token"]},
    )
    assert refresh_response.status_code == 200, refresh_response.text
    refresh_body = refresh_response.json()
    assert refresh_body["access_token"]
    assert refresh_body["refresh_token"]

    logout_response = client.post(
        "/auth/logout",
        json={"refresh_token": refresh_body["refresh_token"]},
    )
    assert logout_response.status_code == 200, logout_response.text

    reused_refresh_response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_body["refresh_token"]},
    )
    assert reused_refresh_response.status_code == 401


def test_openapi_contains_auth_paths() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/auth/register" in paths
    assert "/auth/login" in paths
    assert "/auth/refresh" in paths
    assert "/auth/logout" in paths
    assert "/auth/me" in paths

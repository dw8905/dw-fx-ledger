from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def register_user(client: TestClient, suffix: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": f"posts-{suffix}@example.com",
            "login_id": f"posts_{suffix}",
            "password": "password123",
            "display_name": f"Posts User {suffix}",
            "default_allocation_strategy": "highest_rate_first",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


def test_posts_crud_and_permissions() -> None:
    owner_client = TestClient(app)
    other_client = TestClient(app)
    owner = register_user(owner_client, uuid4().hex[:12])
    register_user(other_client, uuid4().hex[:12])

    create_response = owner_client.post(
        "/posts",
        json={"title": "첫 게시글", "content": "게시글 내용입니다."},
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    post_id = created["postId"]
    assert created["authorId"] == owner["user_id"]
    assert created["postStatus"] == "published"

    list_response = owner_client.get("/posts")
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert list_body["page"] == 1
    assert list_body["size"] == 20
    assert list_body["totalCount"] >= 1
    assert any(item["postId"] == post_id for item in list_body["items"])

    detail_response = owner_client.get(f"/posts/{post_id}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["postId"] == post_id
    assert detail["viewCount"] == 1

    forbidden_update = other_client.put(
        f"/posts/{post_id}",
        json={"title": "권한 없음", "content": "수정 불가"},
    )
    assert forbidden_update.status_code == 403

    forbidden_delete = other_client.delete(f"/posts/{post_id}")
    assert forbidden_delete.status_code == 403

    update_response = owner_client.put(
        f"/posts/{post_id}",
        json={"title": "수정된 제목", "content": "수정된 내용"},
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["title"] == "수정된 제목"
    assert updated["content"] == "수정된 내용"

    delete_response = owner_client.delete(f"/posts/{post_id}")
    assert delete_response.status_code == 200, delete_response.text

    deleted_detail_response = owner_client.get(f"/posts/{post_id}")
    assert deleted_detail_response.status_code == 404


def test_posts_openapi_paths() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/posts" in paths
    assert "/posts/{post_id}" in paths

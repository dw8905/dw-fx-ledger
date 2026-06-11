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
    assert created["boardTypeCode"] == "general"
    assert created["boardTypeName"] == "일반 게시판"
    assert created["postStatus"] == "published"

    list_response = owner_client.get("/posts")
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert list_body["page"] == 1
    assert list_body["size"] == 10
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


def test_post_view_count_increments_once_per_detail_request() -> None:
    client = TestClient(app)
    register_user(client, uuid4().hex[:12])

    create_response = client.post(
        "/posts",
        json={"title": "조회수 테스트", "content": "상세 조회수 검증"},
    )
    assert create_response.status_code == 201, create_response.text
    post_id = create_response.json()["postId"]

    initial_list_response = client.get("/posts")
    assert initial_list_response.status_code == 200, initial_list_response.text
    initial_item = next(
        item for item in initial_list_response.json()["items"] if item["postId"] == post_id
    )
    assert initial_item["viewCount"] == 0

    first_detail_response = client.get(f"/posts/{post_id}")
    assert first_detail_response.status_code == 200, first_detail_response.text
    assert first_detail_response.json()["viewCount"] == 1

    list_after_first_detail_response = client.get("/posts")
    assert list_after_first_detail_response.status_code == 200, list_after_first_detail_response.text
    item_after_first_detail = next(
        item
        for item in list_after_first_detail_response.json()["items"]
        if item["postId"] == post_id
    )
    assert item_after_first_detail["viewCount"] == 1

    second_detail_response = client.get(f"/posts/{post_id}")
    assert second_detail_response.status_code == 200, second_detail_response.text
    assert second_detail_response.json()["viewCount"] == 2


def test_posts_list_pagination_and_keyword_search() -> None:
    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    unique = uuid4().hex[:12]

    first_response = client.post(
        "/posts",
        json={"title": f"검색 대상 {unique}", "content": "첫 번째 검색 본문"},
    )
    assert first_response.status_code == 201, first_response.text
    second_response = client.post(
        "/posts",
        json={"title": f"다른 제목 {unique}", "content": f"본문 키워드 {unique}"},
    )
    assert second_response.status_code == 201, second_response.text

    page_response = client.get("/posts?page=1&size=1")
    assert page_response.status_code == 200, page_response.text
    page_body = page_response.json()
    assert page_body["page"] == 1
    assert page_body["size"] == 1
    assert len(page_body["items"]) == 1
    assert page_body["totalCount"] >= 2

    search_response = client.get(f"/posts?keyword={unique}&page=1&size=20")
    assert search_response.status_code == 200, search_response.text
    searched_ids = {item["postId"] for item in search_response.json()["items"]}
    assert first_response.json()["postId"] in searched_ids
    assert second_response.json()["postId"] in searched_ids


def test_posts_board_type_default_filter_and_invalid_type() -> None:
    client = TestClient(app)
    register_user(client, uuid4().hex[:12])

    board_types_response = client.get("/posts/board-types")
    assert board_types_response.status_code == 200, board_types_response.text
    assert {"code": "general", "name": "일반 게시판"} in board_types_response.json()

    create_response = client.post(
        "/posts",
        json={"title": "기본 게시판 타입", "content": "board type default"},
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["boardTypeCode"] == "general"

    list_response = client.get("/posts?board_type_code=general")
    assert list_response.status_code == 200, list_response.text
    assert any(item["postId"] == created["postId"] for item in list_response.json()["items"])

    invalid_list_response = client.get("/posts?board_type_code=unknown")
    assert invalid_list_response.status_code == 400

    invalid_create_response = client.post(
        "/posts",
        json={
            "title": "잘못된 게시판 타입",
            "content": "invalid board type",
            "boardTypeCode": "unknown",
        },
    )
    assert invalid_create_response.status_code == 400


def test_posts_openapi_paths() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/posts" in paths
    assert "/posts/{post_id}" in paths

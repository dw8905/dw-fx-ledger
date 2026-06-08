from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.main import app
from app.services.auth import get_user_by_identifier
from app.services.roles import ADMIN_ROLE_CODE, ensure_base_roles, grant_admin_role, user_role_count


def require_fx_lot_events_table() -> None:
    if not inspect(engine).has_table("fx_lot_events"):
        pytest.skip("fx_lot_events migration is generated but not applied")


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


def grant_admin(login_id: str) -> None:
    with SessionLocal() as db:
        ensure_base_roles(db)
        user = get_user_by_identifier(db, login_id)
        assert user is not None
        grant_admin_role(db, user=user)
        db.commit()


def test_admin_endpoint_requires_admin_role() -> None:
    user_client = TestClient(app)
    admin_client = TestClient(app)
    user_suffix = uuid4().hex[:12]
    admin_suffix = uuid4().hex[:12]

    register_user(user_client, user_suffix)
    admin = register_user(admin_client, admin_suffix)

    user_response = user_client.get("/admin/health")
    assert user_response.status_code == 403

    grant_admin(admin["login_id"])

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


def test_admin_can_list_users_and_regular_user_cannot() -> None:
    user_client = TestClient(app)
    admin_client = TestClient(app)
    user = register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])

    forbidden_response = user_client.get("/admin/users")
    assert forbidden_response.status_code == 403

    response = admin_client.get("/admin/users?page=1&size=100")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_count"] >= 2
    assert body["total_pages"] >= 1
    listed_user = next(item for item in body["items"] if item["user_id"] == user["user_id"])
    assert listed_user["email"] == user["email"]
    assert "user" in listed_user["roles"]

    detail_response = admin_client.get(f"/admin/users/{user['user_id']}")
    assert detail_response.status_code == 200, detail_response.text
    detail = detail_response.json()
    assert detail["user_id"] == user["user_id"]
    assert "fx_summary" in detail


def test_admin_users_pagination_keyword_and_role_filter() -> None:
    admin_client = TestClient(app)
    user_client = TestClient(app)
    admin = register_user(admin_client, uuid4().hex[:12])
    target_suffix = uuid4().hex[:12]
    target = register_user(user_client, target_suffix)
    grant_admin(admin["login_id"])

    page_response = admin_client.get("/admin/users?page=1&size=1")
    assert page_response.status_code == 200, page_response.text
    page_body = page_response.json()
    assert page_body["page"] == 1
    assert page_body["size"] == 1
    assert len(page_body["items"]) == 1
    assert page_body["total_pages"] >= 2

    keyword_response = admin_client.get(f"/admin/users?keyword={target['login_id']}")
    assert keyword_response.status_code == 200, keyword_response.text
    keyword_body = keyword_response.json()
    assert any(item["user_id"] == target["user_id"] for item in keyword_body["items"])

    admin_role_response = admin_client.get("/admin/users?role=admin&page=1&size=100")
    assert admin_role_response.status_code == 200, admin_role_response.text
    admin_role_body = admin_role_response.json()
    assert any(item["user_id"] == admin["user_id"] for item in admin_role_body["items"])
    assert all("admin" in item["roles"] for item in admin_role_body["items"])

    active_response = admin_client.get("/admin/users?user_status=active&page=1&size=100")
    assert active_response.status_code == 200, active_response.text
    assert all(item["user_status"] == "active" for item in active_response.json()["items"])


def test_admin_can_list_posts() -> None:
    user_client = TestClient(app)
    admin_client = TestClient(app)
    user = register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])

    create_response = user_client.post(
        "/posts",
        json={"title": "Admin posts list", "content": "Read-only admin post audit"},
    )
    assert create_response.status_code == 201, create_response.text
    post_id = create_response.json()["postId"]

    forbidden_response = user_client.get("/admin/posts")
    assert forbidden_response.status_code == 403

    response = admin_client.get("/admin/posts?include_deleted=true&page=1&size=100")
    assert response.status_code == 200, response.text
    item = next(post for post in response.json()["items"] if post["post_id"] == post_id)
    assert item["author_id"] == user["user_id"]
    assert item["title"] == "Admin posts list"
    assert item["is_deleted"] is False


def test_admin_posts_pagination_search_and_status_filter() -> None:
    user_client = TestClient(app)
    admin_client = TestClient(app)
    register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])

    unique = uuid4().hex[:12]
    first_response = user_client.post(
        "/posts",
        json={"title": f"Admin Search {unique}", "content": "visible post body"},
    )
    assert first_response.status_code == 201, first_response.text
    second_response = user_client.post(
        "/posts",
        json={"title": f"Admin Deleted {unique}", "content": "deleted post body"},
    )
    assert second_response.status_code == 201, second_response.text
    deleted_post_id = second_response.json()["postId"]
    delete_response = user_client.delete(f"/posts/{deleted_post_id}")
    assert delete_response.status_code == 200, delete_response.text

    page_response = admin_client.get("/admin/posts?page=1&size=1&include_deleted=true")
    assert page_response.status_code == 200, page_response.text
    page_body = page_response.json()
    assert page_body["size"] == 1
    assert len(page_body["items"]) == 1
    assert page_body["total_pages"] >= 2

    search_response = admin_client.get(f"/admin/posts?keyword={unique}&include_deleted=true")
    assert search_response.status_code == 200, search_response.text
    searched_ids = {item["post_id"] for item in search_response.json()["items"]}
    assert first_response.json()["postId"] in searched_ids
    assert deleted_post_id in searched_ids

    deleted_response = admin_client.get(
        f"/admin/posts?keyword={unique}&post_status=deleted&include_deleted=true"
    )
    assert deleted_response.status_code == 200, deleted_response.text
    deleted_body = deleted_response.json()
    assert any(item["post_id"] == deleted_post_id for item in deleted_body["items"])
    assert all(item["post_status"] == "deleted" for item in deleted_body["items"])


def test_admin_item_codes_crud_and_regular_user_forbidden() -> None:
    if not inspect(engine).has_table("item_codes"):
        pytest.skip("item code migration is generated but not applied")

    user_client = TestClient(app)
    admin_client = TestClient(app)
    register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])
    unique = uuid4().hex[:8]
    item_name = f"디바인스톤 {unique}"

    forbidden_response = user_client.get("/admin/item-codes")
    assert forbidden_response.status_code == 403

    create_response = admin_client.post(
        "/admin/item-codes",
        json={
            "item_name": item_name,
            "memo": "테스트 코드",
            "is_active": True,
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["item_code"].startswith("ITEM-")
    assert created["item_name"] == item_name
    assert created["is_active"] is True

    duplicate_response = admin_client.post(
        "/admin/item-codes",
        json={
            "item_name": item_name,
            "is_active": True,
        },
    )
    assert duplicate_response.status_code == 409

    list_response = admin_client.get(f"/admin/item-codes?keyword={unique}")
    assert list_response.status_code == 200, list_response.text
    assert any(item["item_code_id"] == created["item_code_id"] for item in list_response.json()["items"])

    update_response = admin_client.put(
        f"/admin/item-codes/{created['item_code_id']}",
        json={
            "item_name": f"디바인 스톤 {unique}",
            "memo": "수정",
            "is_active": True,
        },
    )
    assert update_response.status_code == 200, update_response.text
    assert update_response.json()["item_name"] == f"디바인 스톤 {unique}"

    deactivate_response = admin_client.delete(f"/admin/item-codes/{created['item_code_id']}")
    assert deactivate_response.status_code == 200, deactivate_response.text
    assert deactivate_response.json()["is_active"] is False


def test_admin_can_read_user_ledger_and_lot_events() -> None:
    require_fx_lot_events_table()

    user_client = TestClient(app)
    admin_client = TestClient(app)
    user = register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])

    buy_response = user_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert buy_response.status_code == 201, buy_response.text

    sell_response = user_client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-04",
            "sellUsdAmount": "10.00",
            "sellExchangeRate": "1300.00",
            "allocationStrategy": "fifo",
        },
    )
    assert sell_response.status_code == 201, sell_response.text

    forbidden_ledger_response = user_client.get(f"/admin/fx/users/{user['user_id']}/ledger")
    assert forbidden_ledger_response.status_code == 403

    ledger_response = admin_client.get(f"/admin/fx/users/{user['user_id']}/ledger?period=all")
    assert ledger_response.status_code == 200, ledger_response.text
    ledger_body = ledger_response.json()
    assert ledger_body["user"]["user_id"] == user["user_id"]
    assert ledger_body["ledger"]["summary"]["totalRows"] >= 1

    events_response = admin_client.get(
        f"/admin/fx/lot-events?user_id={user['user_id']}&event_type=sell_transaction_created"
    )
    assert events_response.status_code == 200, events_response.text
    events_body = events_response.json()
    assert events_body["total_count"] >= 1
    assert all(event["user_id"] == user["user_id"] for event in events_body["items"])
    assert all(event["event_type"] == "sell_transaction_created" for event in events_body["items"])


def test_admin_lot_events_pagination_and_extra_filters() -> None:
    require_fx_lot_events_table()

    user_client = TestClient(app)
    admin_client = TestClient(app)
    user = register_user(user_client, uuid4().hex[:12])
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])

    buy_response = user_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 2000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert buy_response.status_code == 201, buy_response.text
    root_buy_lot_id = buy_response.json()["buyLotId"]
    sell_response = user_client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-04",
            "sellUsdAmount": "10.00",
            "sellExchangeRate": "1300.00",
            "allocationStrategy": "fifo",
        },
    )
    assert sell_response.status_code == 201, sell_response.text
    sell_transaction_id = sell_response.json()["sellTransactionId"]

    page_response = admin_client.get("/admin/fx/lot-events?page=1&size=1")
    assert page_response.status_code == 200, page_response.text
    page_body = page_response.json()
    assert page_body["size"] == 1
    assert len(page_body["items"]) == 1
    assert page_body["total_pages"] >= 1

    filtered_response = admin_client.get(
        "/admin/fx/lot-events"
        f"?user_id={user['user_id']}"
        f"&sell_transaction_id={sell_transaction_id}"
        f"&root_buy_lot_id={root_buy_lot_id}"
    )
    assert filtered_response.status_code == 200, filtered_response.text
    filtered_body = filtered_response.json()
    assert filtered_body["total_count"] >= 1
    assert all(event["user_id"] == user["user_id"] for event in filtered_body["items"])
    assert all(
        event["sell_transaction_id"] == sell_transaction_id for event in filtered_body["items"]
    )
    assert all(event["root_buy_lot_id"] == root_buy_lot_id for event in filtered_body["items"])

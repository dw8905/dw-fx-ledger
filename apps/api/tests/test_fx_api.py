from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def register_user(client: TestClient, suffix: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": f"fx-{suffix}@example.com",
            "login_id": f"fx_{suffix}",
            "password": "password123",
            "display_name": f"FX User {suffix}",
            "default_allocation_strategy": "highest_rate_first",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


def test_buy_lots_require_auth() -> None:
    client = TestClient(app)
    response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 41675154,
            "buyExchangeRate": "1450.51",
        },
    )
    assert response.status_code == 401


def test_buy_lot_create_list_detail_and_ownership() -> None:
    owner_client = TestClient(app)
    other_client = TestClient(app)
    register_user(owner_client, uuid4().hex[:12])
    register_user(other_client, uuid4().hex[:12])

    create_response = owner_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 41675154,
            "buyExchangeRate": "1450.51",
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["buyDate"] == "2025-03-06"
    assert created["buyKrwAmount"] == 41675154
    assert created["buyExchangeRate"] == "1450.510000"
    assert Decimal(created["usdAmount"]) == Decimal("28731.379997")
    assert created["lotStatus"] == "open"
    assert created["isActive"] is True

    second_response = owner_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-07",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1400.00",
        },
    )
    assert second_response.status_code == 201, second_response.text

    list_response = owner_client.get("/fx/buy-lots?page=1&size=1")
    assert list_response.status_code == 200, list_response.text
    list_body = list_response.json()
    assert list_body["page"] == 1
    assert list_body["size"] == 1
    assert list_body["totalCount"] >= 2
    assert len(list_body["items"]) == 1

    filtered_response = owner_client.get("/fx/buy-lots?lot_status=open&is_active=true")
    assert filtered_response.status_code == 200, filtered_response.text
    assert filtered_response.json()["totalCount"] >= 2

    detail_response = owner_client.get(f"/fx/buy-lots/{created['buyLotId']}")
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["buyLotId"] == created["buyLotId"]

    other_detail_response = other_client.get(f"/fx/buy-lots/{created['buyLotId']}")
    assert other_detail_response.status_code == 404

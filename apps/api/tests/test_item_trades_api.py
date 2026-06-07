from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.session import SessionLocal, engine
from app.main import app
from app.services.auth import get_user_by_identifier
from app.services.roles import ensure_base_roles, grant_admin_role


def require_item_tables() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("item_trades") or not inspector.has_table("item_codes"):
        pytest.skip("item trade migrations are generated but not applied")


def register_user(client: TestClient, suffix: str) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "email": f"item-{suffix}@example.com",
            "login_id": f"item_{suffix}",
            "password": "password123",
            "display_name": f"Item User {suffix}",
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


def create_admin_item_code(item_name: str = "디바인스톤") -> str:
    admin_client = TestClient(app)
    admin = register_user(admin_client, uuid4().hex[:12])
    grant_admin(admin["login_id"])
    response = admin_client.post(
        "/admin/item-codes",
        json={
            "item_name": item_name,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["item_code"]


def test_item_trades_require_auth() -> None:
    require_item_tables()

    client = TestClient(app)
    response = client.get("/item-trades")
    assert response.status_code == 401


def test_regular_user_cannot_create_item_code() -> None:
    require_item_tables()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    response = client.post(
        "/item-trades/item-codes",
        json={"itemCode": "DIVINE_STONE", "itemName": "디바인스톤"},
    )
    assert response.status_code == 405


def test_average_cost_buy_sell_summary_and_fee_rate() -> None:
    require_item_tables()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    item_code = create_admin_item_code()

    first_buy = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "buy",
            "tradeDate": "2026-06-06",
            "unitPrice": 1000000,
            "quantity": 100,
            "feeRate": "0.05",
        },
    )
    assert first_buy.status_code == 201, first_buy.text
    assert first_buy.json()["feeRate"] == "0.050000"
    assert first_buy.json()["averageBuyUnitPrice"] == 1000000
    assert first_buy.json()["minimumProfitableUnitPrice"] == 1052632

    second_buy = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "buy",
            "tradeDate": "2026-06-07",
            "unitPrice": 1100000,
            "quantity": 100,
            "feeRate": "0.05",
        },
    )
    assert second_buy.status_code == 201, second_buy.text
    body = second_buy.json()
    assert body["inventoryQuantityAfter"] == 200
    assert body["inventoryValueAfter"] == 210000000
    assert body["averageBuyUnitPrice"] == 1050000
    assert body["feeRate"] == "0.050000"
    assert body["minimumProfitableUnitPrice"] == 1105264

    sell = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "sell",
            "tradeDate": "2026-06-08",
            "unitPrice": 1200000,
            "quantity": 50,
            "feeRate": "0.05",
        },
    )
    assert sell.status_code == 201, sell.text
    sold = sell.json()
    assert sold["tradeType"] == "sell"
    assert sold["feeRate"] == "0.050000"
    assert sold["averageBuyUnitPrice"] == 1050000
    assert sold["totalBuyAmount"] == 52500000
    assert sold["totalSellAmount"] == 60000000
    assert sold["feeAmount"] == 3000000
    assert sold["netSellAmount"] == 57000000
    assert sold["profitAmount"] == 4500000
    assert sold["inventoryQuantityAfter"] == 150
    assert sold["inventoryValueAfter"] == 157500000

    list_response = client.get("/item-trades?page=1&size=10")
    assert list_response.status_code == 200, list_response.text
    listed = list_response.json()
    assert listed["totalCount"] == 3
    assert listed["items"][0]["tradeType"] == "sell"
    assert listed["items"][0]["feeRate"] == "0.050000"
    summary = next(item for item in listed["summaries"] if item["itemCode"] == item_code)
    assert summary["inventoryQuantity"] == 150
    assert summary["averageBuyUnitPrice"] == 1050000
    assert summary["minimumProfitableUnitPrice"] == 1105264
    assert summary["totalProfitAmount"] == 4500000


def test_inventory_summary_defaults_zero_fee_to_five_percent() -> None:
    require_item_tables()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    item_code = create_admin_item_code("카오스코어")

    buy = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "카오스코어",
            "tradeType": "buy",
            "tradeDate": "2026-06-07",
            "unitPrice": 925555,
            "quantity": 12,
            "feeRate": "0",
        },
    )
    assert buy.status_code == 201, buy.text

    list_response = client.get("/item-trades?page=1&size=10")
    assert list_response.status_code == 200, list_response.text
    summary = next(item for item in list_response.json()["summaries"] if item["itemCode"] == item_code)
    assert summary["averageBuyUnitPrice"] == 925555
    assert summary["minimumProfitableUnitPrice"] == 974269


def test_sell_rejects_insufficient_inventory_and_user_scope() -> None:
    require_item_tables()

    owner_client = TestClient(app)
    other_client = TestClient(app)
    register_user(owner_client, uuid4().hex[:12])
    register_user(other_client, uuid4().hex[:12])
    item_code = create_admin_item_code()

    create_response = owner_client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "buy",
            "tradeDate": "2026-06-06",
            "unitPrice": 1000,
            "quantity": 1,
            "feeRate": "0.05",
        },
    )
    assert create_response.status_code == 201, create_response.text

    blocked_sell = owner_client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "sell",
            "tradeDate": "2026-06-07",
            "unitPrice": 1200,
            "quantity": 2,
            "feeRate": "0.05",
        },
    )
    assert blocked_sell.status_code == 400

    other_list = other_client.get("/item-trades")
    assert other_list.status_code == 200, other_list.text
    assert other_list.json()["totalCount"] == 0
    assert other_list.json()["summaries"] == []


def test_item_trade_cancel_recalculates_inventory_and_blocks_invalid_buy_cancel() -> None:
    require_item_tables()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    item_code = create_admin_item_code()

    first_buy = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "buy",
            "tradeDate": "2026-06-06",
            "unitPrice": 1000,
            "quantity": 10,
            "feeRate": "0.05",
        },
    )
    assert first_buy.status_code == 201, first_buy.text
    second_buy = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "buy",
            "tradeDate": "2026-06-07",
            "unitPrice": 2000,
            "quantity": 10,
            "feeRate": "0.05",
        },
    )
    assert second_buy.status_code == 201, second_buy.text
    sell = client.post(
        "/item-trades",
        json={
            "itemCode": item_code,
            "itemName": "디바인스톤",
            "tradeType": "sell",
            "tradeDate": "2026-06-08",
            "unitPrice": 2500,
            "quantity": 15,
            "feeRate": "0.05",
        },
    )
    assert sell.status_code == 201, sell.text

    blocked_cancel = client.post(
        f"/item-trades/{first_buy.json()['itemTradeId']}/cancel",
        json={"cancelReason": "would break later sell"},
    )
    assert blocked_cancel.status_code == 409

    cancel_sell = client.post(
        f"/item-trades/{sell.json()['itemTradeId']}/cancel",
        json={"cancelReason": "wrong sell"},
    )
    assert cancel_sell.status_code == 200, cancel_sell.text
    assert cancel_sell.json()["tradeStatus"] == "cancelled"

    after_sell_cancel = client.get("/item-trades")
    assert after_sell_cancel.status_code == 200, after_sell_cancel.text
    summary = next(item for item in after_sell_cancel.json()["summaries"] if item["itemCode"] == item_code)
    assert summary["inventoryQuantity"] == 20
    assert summary["inventoryValue"] == 30000
    assert summary["averageBuyUnitPrice"] == 1500
    assert summary["totalProfitAmount"] == 0

    cancel_first_buy = client.post(
        f"/item-trades/{first_buy.json()['itemTradeId']}/cancel",
        json={"cancelReason": "wrong buy"},
    )
    assert cancel_first_buy.status_code == 200, cancel_first_buy.text

    final_list = client.get("/item-trades")
    assert final_list.status_code == 200, final_list.text
    final_summary = next(item for item in final_list.json()["summaries"] if item["itemCode"] == item_code)
    assert final_summary["inventoryQuantity"] == 10
    assert final_summary["inventoryValue"] == 20000
    assert final_summary["averageBuyUnitPrice"] == 2000
    assert final_summary["totalProfitAmount"] == 0
    cancelled_ids = {
        item["itemTradeId"]
        for item in final_list.json()["items"]
        if item["tradeStatus"] == "cancelled"
    }
    assert sell.json()["itemTradeId"] in cancelled_ids
    assert first_buy.json()["itemTradeId"] in cancelled_ids

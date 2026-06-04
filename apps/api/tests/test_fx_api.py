from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.db.session import engine
from app.main import app


def require_fx_lot_events_table() -> None:
    if not inspect(engine).has_table("fx_lot_events"):
        pytest.skip("fx_lot_events migration is generated but not applied")


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


def test_buy_lot_update_open_only() -> None:
    owner_client = TestClient(app)
    other_client = TestClient(app)
    register_user(owner_client, uuid4().hex[:12])
    register_user(other_client, uuid4().hex[:12])

    create_response = owner_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert create_response.status_code == 201, create_response.text
    buy_lot_id = create_response.json()["buyLotId"]

    other_update_response = other_client.put(
        f"/fx/buy-lots/{buy_lot_id}",
        json={
            "buyDate": "2025-03-07",
            "buyKrwAmount": 2000000,
            "buyExchangeRate": "1200.00",
        },
    )
    assert other_update_response.status_code == 404

    update_response = owner_client.put(
        f"/fx/buy-lots/{buy_lot_id}",
        json={
            "buyDate": "2025-03-07",
            "buyKrwAmount": 2000000,
            "buyExchangeRate": "1200.00",
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["buyDate"] == "2025-03-07"
    assert updated["buyKrwAmount"] == 2000000
    assert updated["buyExchangeRate"] == "1200.000000"
    assert updated["usdAmount"] == "1666.666667"

    require_fx_lot_events_table()

    sell_response = owner_client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-04",
            "sellUsdAmount": "10.00",
            "sellExchangeRate": "1300.00",
            "allocationStrategy": "fifo",
        },
    )
    assert sell_response.status_code == 201, sell_response.text

    update_split_response = owner_client.put(
        f"/fx/buy-lots/{buy_lot_id}",
        json={
            "buyDate": "2025-03-08",
            "buyKrwAmount": 3000000,
            "buyExchangeRate": "1300.00",
        },
    )
    assert update_split_response.status_code == 409


def test_buy_lots_sorting() -> None:
    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    lots = [
        ("2025-03-06", 1000000, "1450.51"),
        ("2025-03-07", 1000000, "1400.00"),
        ("2025-03-08", 1000000, "1500.00"),
    ]
    for buy_date, amount, rate in lots:
        response = client.post(
            "/fx/buy-lots",
            json={
                "buyDate": buy_date,
                "buyKrwAmount": amount,
                "buyExchangeRate": rate,
            },
        )
        assert response.status_code == 201, response.text

    asc_response = client.get("/fx/buy-lots?sort_by=buy_exchange_rate&sort_order=asc")
    assert asc_response.status_code == 200, asc_response.text
    asc_rates = [Decimal(item["buyExchangeRate"]) for item in asc_response.json()["items"][:3]]
    assert asc_rates == sorted(asc_rates)

    desc_response = client.get(
        "/fx/buy-lots?sort_by=buy_exchange_rate&sort_order=desc&page=1&size=2"
    )
    assert desc_response.status_code == 200, desc_response.text
    desc_body = desc_response.json()
    desc_rates = [Decimal(item["buyExchangeRate"]) for item in desc_body["items"]]
    assert desc_rates == sorted(desc_rates, reverse=True)
    assert desc_body["size"] == 2


def test_buy_lot_delete_open_without_events_success() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    create_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()

    delete_response = client.delete(f"/fx/buy-lots/{created['buyLotId']}")
    assert delete_response.status_code == 200, delete_response.text
    deleted = delete_response.json()
    assert deleted["buyLotId"] == created["buyLotId"]
    assert deleted["lotStatus"] == "cancelled"
    assert deleted["isActive"] is False

    detail_response = client.get(f"/fx/buy-lots/{created['buyLotId']}")
    assert detail_response.status_code == 404

    list_response = client.get("/fx/buy-lots")
    assert list_response.status_code == 200, list_response.text
    listed_ids = {item["buyLotId"] for item in list_response.json()["items"]}
    assert created["buyLotId"] not in listed_ids


def test_buy_lot_delete_rejects_other_user() -> None:
    require_fx_lot_events_table()

    owner_client = TestClient(app)
    other_client = TestClient(app)
    register_user(owner_client, uuid4().hex[:12])
    register_user(other_client, uuid4().hex[:12])

    create_response = owner_client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert create_response.status_code == 201, create_response.text

    delete_response = other_client.delete(
        f"/fx/buy-lots/{create_response.json()['buyLotId']}"
    )
    assert delete_response.status_code == 404


def test_buy_lot_delete_rejects_used_split_sold_and_cancelled_lots() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    source_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert source_response.status_code == 201, source_response.text
    source = source_response.json()

    sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "100.00",
            "sellExchangeRate": "1200.00",
            "allocationStrategy": "fifo",
        },
    )
    assert sell_response.status_code == 201, sell_response.text
    allocation = sell_response.json()["allocations"][0]

    split_delete_response = client.delete(f"/fx/buy-lots/{source['buyLotId']}")
    assert split_delete_response.status_code == 409

    sold_delete_response = client.delete(f"/fx/buy-lots/{allocation['closedBuyLotId']}")
    assert sold_delete_response.status_code == 409

    cancel_response = client.post(
        f"/fx/sell-transactions/{sell_response.json()['sellTransactionId']}/cancel",
        json={"cancelReason": "delete test"},
    )
    assert cancel_response.status_code == 200, cancel_response.text

    cancelled_delete_response = client.delete(
        f"/fx/buy-lots/{allocation['closedBuyLotId']}"
    )
    assert cancelled_delete_response.status_code == 409


def test_sell_transaction_split_allocation_and_rollback() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    source_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 41675154,
            "buyExchangeRate": "1450.51",
        },
    )
    assert source_response.status_code == 201, source_response.text
    source = source_response.json()

    sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-04",
            "sellUsdAmount": "214.93",
            "sellExchangeRate": "1531.33",
            "allocationStrategy": "highest_rate_first",
        },
    )
    assert sell_response.status_code == 201, sell_response.text
    sell = sell_response.json()
    assert sell["sellUsdAmount"] == "214.930000"
    assert sell["totalBuyKrwAmount"] == 311759
    assert sell["totalSellKrwAmount"] == 329130
    assert sell["totalRealProfitKrw"] == 17371
    assert len(sell["allocations"]) == 1
    allocation = sell["allocations"][0]
    assert allocation["sourceBuyLotId"] == source["buyLotId"]
    assert allocation["remainingBuyLotId"] is not None

    source_after = client.get(f"/fx/buy-lots/{source['buyLotId']}").json()
    assert source_after["lotStatus"] == "split"
    assert source_after["isActive"] is False

    lots_response = client.get("/fx/buy-lots?sort_by=created_at&sort_order=asc")
    assert lots_response.status_code == 200, lots_response.text
    lots = lots_response.json()["items"]
    sold_lot = next(item for item in lots if item["buyLotId"] == allocation["closedBuyLotId"])
    remaining_lot = next(item for item in lots if item["buyLotId"] == allocation["remainingBuyLotId"])
    assert sold_lot["lotStatus"] == "sold"
    assert sold_lot["isActive"] is False
    assert remaining_lot["lotStatus"] == "open"
    assert remaining_lot["isActive"] is True

    too_much_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "999999999.00",
            "sellExchangeRate": "1531.33",
            "allocationStrategy": "fifo",
        },
    )
    assert too_much_response.status_code == 400


def test_sell_transactions_multi_lot_and_sorting() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    for buy_date, amount, rate in [
        ("2025-03-01", 100000, "1000.00"),
        ("2025-03-02", 100000, "2000.00"),
        ("2025-03-03", 100000, "1500.00"),
    ]:
        response = client.post(
            "/fx/buy-lots",
            json={"buyDate": buy_date, "buyKrwAmount": amount, "buyExchangeRate": rate},
        )
        assert response.status_code == 201, response.text

    sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "110.00",
            "sellExchangeRate": "2100.00",
            "allocationStrategy": "highest_rate_first",
        },
    )
    assert sell_response.status_code == 201, sell_response.text
    assert len(sell_response.json()["allocations"]) == 2

    second_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-06",
            "sellUsdAmount": "10.00",
            "sellExchangeRate": "1800.00",
            "allocationStrategy": "lifo",
        },
    )
    assert second_sell_response.status_code == 201, second_sell_response.text

    asc_response = client.get(
        "/fx/sell-transactions?sort_by=total_real_profit_krw&sort_order=asc&page=1&size=2"
    )
    assert asc_response.status_code == 200, asc_response.text
    profits = [item["totalRealProfitKrw"] for item in asc_response.json()["items"]]
    assert profits == sorted(profits)

    desc_response = client.get(
        "/fx/sell-transactions?sort_by=total_real_profit_krw&sort_order=desc"
    )
    assert desc_response.status_code == 200, desc_response.text
    desc_profits = [item["totalRealProfitKrw"] for item in desc_response.json()["items"]]
    assert desc_profits == sorted(desc_profits, reverse=True)


def test_sell_transaction_cancel_latest_only_and_events() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-06",
            "buyKrwAmount": 1000000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert buy_response.status_code == 201, buy_response.text

    first_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "100.00",
            "sellExchangeRate": "1200.00",
            "allocationStrategy": "fifo",
            "memo": "first sell",
        },
    )
    assert first_sell_response.status_code == 201, first_sell_response.text
    first_sell = first_sell_response.json()

    second_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-06",
            "sellUsdAmount": "100.00",
            "sellExchangeRate": "1300.00",
            "allocationStrategy": "fifo",
        },
    )
    assert second_sell_response.status_code == 201, second_sell_response.text
    second_sell = second_sell_response.json()

    blocked_cancel_response = client.post(
        f"/fx/sell-transactions/{first_sell['sellTransactionId']}/cancel",
        json={"cancelReason": "middle cancel should fail"},
    )
    assert blocked_cancel_response.status_code == 409

    cancel_response = client.post(
        f"/fx/sell-transactions/{second_sell['sellTransactionId']}/cancel",
        json={"cancelReason": "latest cancel"},
    )
    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["transactionStatus"] == "cancelled"

    first_cancel_response = client.post(
        f"/fx/sell-transactions/{first_sell['sellTransactionId']}/cancel",
        json={"cancelReason": "now latest"},
    )
    assert first_cancel_response.status_code == 200, first_cancel_response.text
    assert first_cancel_response.json()["transactionStatus"] == "cancelled"

    events_response = client.get("/fx/lot-events?page=1&size=20")
    assert events_response.status_code == 200, events_response.text
    event_types = {event["eventType"] for event in events_response.json()["items"]}
    assert "sell_transaction_created" in event_types
    assert "lot_split" in event_types
    assert "sell_transaction_cancelled" in event_types
    assert "lot_restored" in event_types

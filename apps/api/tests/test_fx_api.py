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


def test_jpy_buy_sell_and_ledger_are_separated_from_usd() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])

    jpy_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "currencyCode": "JPY",
            "buyDate": "2023-06-05",
            "buyKrwAmount": 4999995,
            "buyExchangeRate": "934.68",
        },
    )
    assert jpy_buy_response.status_code == 201, jpy_buy_response.text
    jpy_buy = jpy_buy_response.json()
    assert jpy_buy["currencyCode"] == "JPY"
    assert jpy_buy["quoteUnit"] == "100"
    assert jpy_buy["usdAmount"] == "534941.905251"

    default_usd_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2024-12-03",
            "sellUsdAmount": "100000.00",
            "sellExchangeRate": "954.65",
            "allocationStrategy": "highest_rate_first",
        },
    )
    assert default_usd_sell_response.status_code == 400

    jpy_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "currencyCode": "JPY",
            "sellDate": "2024-12-03",
            "sellUsdAmount": "100000.00",
            "sellExchangeRate": "954.65",
            "allocationStrategy": "highest_rate_first",
        },
    )
    assert jpy_sell_response.status_code == 201, jpy_sell_response.text
    jpy_sell = jpy_sell_response.json()
    assert jpy_sell["currencyCode"] == "JPY"
    assert jpy_sell["totalBuyKrwAmount"] == 934680
    assert jpy_sell["totalSellKrwAmount"] == 954650
    assert jpy_sell["totalRealProfitKrw"] == 19970

    usd_ledger_response = client.get("/fx/ledger?period=all")
    assert usd_ledger_response.status_code == 200, usd_ledger_response.text
    assert usd_ledger_response.json()["summary"]["currencyCode"] == "USD"
    assert usd_ledger_response.json()["summary"]["totalRows"] == 0

    jpy_ledger_response = client.get("/fx/ledger?period=all&currencyCode=JPY")
    assert jpy_ledger_response.status_code == 200, jpy_ledger_response.text
    jpy_ledger = jpy_ledger_response.json()
    assert jpy_ledger["summary"]["currencyCode"] == "JPY"
    assert jpy_ledger["summary"]["totalOpenUsdAmount"] == "434941.905251"
    assert jpy_ledger["summary"]["finalCumulativeProfitKrw"] == 19970


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


def test_sell_transaction_manual_allocations() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    first_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-01",
            "buyKrwAmount": 100000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert first_buy_response.status_code == 201, first_buy_response.text
    second_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-03-02",
            "buyKrwAmount": 100000,
            "buyExchangeRate": "2000.00",
        },
    )
    assert second_buy_response.status_code == 201, second_buy_response.text

    first_lot = first_buy_response.json()
    second_lot = second_buy_response.json()
    sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "70.00",
            "sellExchangeRate": "1500.00",
            "allocationStrategy": "manual",
            "manualAllocations": [
                {"buyLotId": first_lot["buyLotId"], "usdAmount": "40.00"},
                {"buyLotId": second_lot["buyLotId"], "usdAmount": "30.00"},
            ],
        },
    )
    assert sell_response.status_code == 201, sell_response.text
    sell = sell_response.json()
    assert sell["allocationStrategy"] == "manual"
    assert sell["sellUsdAmount"] == "70.000000"
    assert len(sell["allocations"]) == 2
    assert [allocation["sourceBuyLotId"] for allocation in sell["allocations"]] == [
        first_lot["buyLotId"],
        second_lot["buyLotId"],
    ]
    assert [allocation["allocatedUsdAmount"] for allocation in sell["allocations"]] == [
        "40.000000",
        "30.000000",
    ]

    mismatch_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-06",
            "sellUsdAmount": "10.00",
            "sellExchangeRate": "1500.00",
            "allocationStrategy": "manual",
            "manualAllocations": [
                {"buyLotId": sell["allocations"][0]["remainingBuyLotId"], "usdAmount": "9.00"},
            ],
        },
    )
    assert mismatch_response.status_code == 400


def test_ledger_open_sold_cumulative_average_and_periods() -> None:
    require_fx_lot_events_table()

    client = TestClient(app)
    register_user(client, uuid4().hex[:12])
    first_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2024-01-01",
            "buyKrwAmount": 100000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert first_buy_response.status_code == 201, first_buy_response.text
    old_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2023-01-01",
            "buyKrwAmount": 100000,
            "buyExchangeRate": "1000.00",
        },
    )
    assert old_buy_response.status_code == 201, old_buy_response.text
    second_buy_response = client.post(
        "/fx/buy-lots",
        json={
            "buyDate": "2025-01-01",
            "buyKrwAmount": 200000,
            "buyExchangeRate": "2000.00",
        },
    )
    assert second_buy_response.status_code == 201, second_buy_response.text

    first_lot = first_buy_response.json()
    old_lot = old_buy_response.json()
    second_lot = second_buy_response.json()
    old_sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2024-06-05",
            "sellUsdAmount": "50.00",
            "sellExchangeRate": "1100.00",
            "allocationStrategy": "manual",
            "manualAllocations": [
                {"buyLotId": old_lot["buyLotId"], "usdAmount": "50.00"},
            ],
        },
    )
    assert old_sell_response.status_code == 201, old_sell_response.text

    sell_response = client.post(
        "/fx/sell-transactions",
        json={
            "sellDate": "2026-06-05",
            "sellUsdAmount": "50.00",
            "sellExchangeRate": "1100.00",
            "allocationStrategy": "manual",
            "manualAllocations": [
                {"buyLotId": first_lot["buyLotId"], "usdAmount": "50.00"},
            ],
        },
    )
    assert sell_response.status_code == 201, sell_response.text

    all_response = client.get("/fx/ledger?period=all")
    assert all_response.status_code == 200, all_response.text
    ledger = all_response.json()
    assert ledger["summary"]["totalRows"] == 5
    assert ledger["summary"]["visibleRows"] == 5
    assert ledger["summary"]["openLotCount"] == 3
    assert ledger["summary"]["totalOpenUsdAmount"] == "200.000000"
    assert ledger["summary"]["soldAllocationCount"] == 2
    assert ledger["summary"]["totalSellTransactionCount"] == 2
    assert ledger["summary"]["totalDisplayProfitKrw"] == 10000
    assert ledger["summary"]["finalCumulativeProfitKrw"] == 10000
    assert ledger["summary"]["latestLedgerDate"] == "2026-06-05"

    sold_rows = [item for item in ledger["items"] if item["lotAllocationId"] is not None]
    open_rows = [item for item in ledger["items"] if item["lotAllocationId"] is None]
    assert len(sold_rows) == 2
    assert len(open_rows) == 3
    sold = next(row for row in sold_rows if row["sellDate"] == "2026-06-05")
    assert sold["buyKrwAmount"] == 50000
    assert sold["sellKrwAmount"] == 55000
    assert sold["profitKrw"] == 5000
    assert sold["exchangeDiff"] == "100.000000"
    assert sold["exchangeDiffAverage"] == "100.000000"
    assert sold["cumulativeProfitKrw"] == 10000
    assert {item["lotStatus"] for item in ledger["items"]} == {"sold", "open"}
    assert second_lot["buyLotId"] in {item["buyLotId"] for item in open_rows}

    latest_response = client.get("/fx/ledger?period=latest")
    assert latest_response.status_code == 200, latest_response.text
    latest = latest_response.json()
    assert latest["summary"]["totalRows"] == 5
    assert latest["summary"]["visibleRows"] == 1
    assert latest["summary"]["totalDisplayProfitKrw"] == 5000
    assert latest["summary"]["finalCumulativeProfitKrw"] == 10000
    assert latest["items"][0]["sellDate"] == "2026-06-05"
    assert latest["items"][0]["cumulativeProfitKrw"] == 10000

    one_year_response = client.get("/fx/ledger?period=1y")
    assert one_year_response.status_code == 200, one_year_response.text
    one_year = one_year_response.json()
    assert one_year["summary"]["totalRows"] == 5
    assert one_year["summary"]["visibleRows"] == 1
    assert one_year["summary"]["totalDisplayProfitKrw"] == 5000
    assert one_year["summary"]["finalCumulativeProfitKrw"] == 10000
    assert one_year["items"][0]["exchangeDiffAverage"] == "100.000000"

    three_year_response = client.get("/fx/ledger?period=3y")
    assert three_year_response.status_code == 200, three_year_response.text
    three_year = three_year_response.json()
    assert three_year["summary"]["visibleRows"] == 4
    assert three_year["summary"]["totalDisplayProfitKrw"] == 10000
    assert three_year["summary"]["finalCumulativeProfitKrw"] == 10000

    five_year_response = client.get("/fx/ledger?period=5y")
    assert five_year_response.status_code == 200, five_year_response.text
    five_year = five_year_response.json()
    assert five_year["summary"]["visibleRows"] == 5
    assert five_year["summary"]["totalDisplayProfitKrw"] == 10000


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

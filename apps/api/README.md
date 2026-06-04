# DW FX Ledger API

FastAPI application scaffold for DW FX Ledger.

## Development

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The API currently exposes only `GET /health`.

## FX ledger persistence note

`fx_buy_lots` stores buy-lot lineage and current lot state only. Sell details are stored in
`fx_sell_transactions` and `fx_lot_allocations` to avoid duplicated sell data.

Excel-like ledger rows should be composed later with a database view, query layer, or API DTO that
joins buy lots, sell transactions, and lot allocations.

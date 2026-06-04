# DW FX Ledger API

FastAPI application scaffold for DW FX Ledger.

## Development

```bash
uv sync
uv run uvicorn app.main:app --reload
```

The API currently exposes only `GET /health`.

## Authentication

Implemented endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /auth/me`

Access tokens are JWT bearer tokens. Refresh tokens are stored as SHA-256 hashes in
`refresh_tokens` and rotated when `/auth/refresh` succeeds.

Required environment variables:

```bash
DATABASE_URL=postgresql+psycopg://...
SECRET_KEY=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
```

Run the API:

```bash
uv run uvicorn app.main:app --reload
```

OpenAPI docs:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/openapi.json
```

Run authentication tests:

```bash
uv run pytest -q tests/test_auth_api.py
```

## FX ledger persistence note

`fx_buy_lots` stores buy-lot lineage and current lot state only. Sell details are stored in
`fx_sell_transactions` and `fx_lot_allocations` to avoid duplicated sell data.

Excel-like ledger rows should be composed later with a database view, query layer, or API DTO that
joins buy lots, sell transactions, and lot allocations.

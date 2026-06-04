from fastapi import FastAPI

app = FastAPI(title="DW FX Ledger API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

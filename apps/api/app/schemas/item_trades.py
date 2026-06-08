from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ItemCodeCreateRequest(BaseModel):
    itemCode: str = Field(min_length=1, max_length=80)
    itemName: str = Field(min_length=1, max_length=120)
    memo: str | None = None


class ItemCodeRead(BaseModel):
    itemCodeId: int
    itemCode: str
    itemName: str
    memo: str | None
    isActive: bool
    createdAt: datetime


class ItemCodeListResponse(BaseModel):
    items: list[ItemCodeRead]


class ItemTradeCreateRequest(BaseModel):
    itemCode: str = Field(min_length=1, max_length=80)
    itemName: str = Field(min_length=1, max_length=120)
    tradeType: str = Field(pattern="^(buy|sell|adjustment)$")
    tradeDate: date
    unitPrice: int = Field(ge=1)
    quantity: int
    feeRate: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), lt=Decimal("1"))
    memo: str | None = None


class ItemTradeCancelRequest(BaseModel):
    cancelReason: str | None = None


class ItemTradeRead(BaseModel):
    itemTradeId: int
    itemCodeId: int | None
    itemCode: str | None
    itemName: str
    tradeType: str
    tradeStatus: str
    tradeDate: date
    unitPrice: int
    quantity: int
    feeRate: Decimal
    minimumProfitableUnitPrice: int
    averageBuyUnitPrice: int | None
    inventoryQuantityAfter: int | None
    inventoryValueAfter: int | None
    buyDate: date
    buyUnitPrice: int
    sellDate: date | None
    sellUnitPrice: int | None
    totalBuyAmount: int
    totalSellAmount: int | None
    feeAmount: int | None
    netSellAmount: int | None
    profitAmount: int | None
    cancelledAt: datetime | None
    cancelReason: str | None
    memo: str | None
    createdAt: datetime


class ItemCodeSummary(BaseModel):
    itemCodeId: int
    itemCode: str
    itemName: str
    inventoryQuantity: int
    inventoryValue: int
    averageBuyUnitPrice: int
    minimumProfitableUnitPrice: int
    totalProfitAmount: int


class ItemTradeListResponse(BaseModel):
    items: list[ItemTradeRead]
    summaries: list[ItemCodeSummary]
    page: int
    size: int
    totalCount: int

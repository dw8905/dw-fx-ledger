from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BuyLotCreateRequest(BaseModel):
    buyDate: date
    buyKrwAmount: int = Field(gt=0)
    buyExchangeRate: Decimal = Field(gt=0)


class BuyLotUpdateRequest(BaseModel):
    buyDate: date
    buyKrwAmount: int = Field(gt=0)
    buyExchangeRate: Decimal = Field(gt=0)


class BuyLotRead(BaseModel):
    buyLotId: int
    buyDate: date
    buyKrwAmount: int
    buyExchangeRate: Decimal
    usdAmount: Decimal
    lotStatus: str
    isActive: bool
    createdAt: datetime


class BuyLotListResponse(BaseModel):
    items: list[BuyLotRead]
    page: int
    size: int
    totalCount: int


class SellTransactionCreateRequest(BaseModel):
    sellDate: date
    sellUsdAmount: Decimal = Field(gt=0)
    sellExchangeRate: Decimal = Field(gt=0)
    allocationStrategy: str | None = Field(default=None, pattern="^(highest_rate_first|fifo|lifo)$")
    memo: str | None = None


class SellTransactionCancelRequest(BaseModel):
    cancelReason: str = Field(min_length=1, max_length=500)


class LotAllocationRead(BaseModel):
    lotAllocationId: int
    sourceBuyLotId: int
    closedBuyLotId: int
    remainingBuyLotId: int | None
    allocatedUsdAmount: Decimal
    allocatedBuyKrwAmount: int
    allocatedSellKrwAmount: int
    realProfitKrw: int
    displayProfitKrw: int
    exchangeDiff: Decimal


class SellTransactionRead(BaseModel):
    sellTransactionId: int
    sellDate: date
    sellUsdAmount: Decimal
    sellExchangeRate: Decimal
    allocationStrategy: str
    transactionStatus: str
    totalBuyKrwAmount: int
    totalSellKrwAmount: int
    totalRealProfitKrw: int
    totalDisplayProfitKrw: int
    memo: str | None
    createdAt: datetime
    allocations: list[LotAllocationRead] = Field(default_factory=list)


class SellTransactionListItem(BaseModel):
    sellTransactionId: int
    sellDate: date
    sellUsdAmount: Decimal
    sellExchangeRate: Decimal
    allocationStrategy: str
    transactionStatus: str
    totalBuyKrwAmount: int
    totalSellKrwAmount: int
    totalRealProfitKrw: int
    totalDisplayProfitKrw: int
    memo: str | None
    createdAt: datetime


class SellTransactionListResponse(BaseModel):
    items: list[SellTransactionListItem]
    page: int
    size: int
    totalCount: int


class LotEventRead(BaseModel):
    lotEventId: int
    eventType: str
    eventStatus: str
    rootBuyLotId: int | None
    sellTransactionId: int | None
    lotAllocationId: int | None
    sourceBuyLotId: int | None
    closedBuyLotId: int | None
    remainingBuyLotId: int | None
    restoredBuyLotId: int | None
    relatedEventId: int | None
    eventPayload: dict | None
    createdAt: datetime


class LotEventListResponse(BaseModel):
    items: list[LotEventRead]
    page: int
    size: int
    totalCount: int

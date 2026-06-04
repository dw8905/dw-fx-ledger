from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BuyLotCreateRequest(BaseModel):
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

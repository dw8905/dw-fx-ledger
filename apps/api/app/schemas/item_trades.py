from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ItemCodeCreateRequest(BaseModel):
    """사용자 거래 화면에서 자산 코드를 만들 때 쓰는 입력 모델입니다."""

    itemCode: str = Field(min_length=1, max_length=80)
    itemName: str = Field(min_length=1, max_length=120)
    memo: str | None = None


class ItemCodeRead(BaseModel):
    """자산 코드 자동완성/선택 목록에 필요한 마스터 정보입니다."""

    itemCodeId: int
    itemCode: str
    itemName: str
    memo: str | None
    isActive: bool
    createdAt: datetime


class ItemCodeListResponse(BaseModel):
    """자산 코드 목록 응답을 items 배열로 감싸는 모델입니다."""

    items: list[ItemCodeRead]


class ItemTradeCreateRequest(BaseModel):
    """자산 매수, 매도, 재고조정 등록 요청을 하나의 형태로 검증합니다."""

    itemCode: str = Field(min_length=1, max_length=80)
    itemName: str = Field(min_length=1, max_length=120)
    tradeType: str = Field(pattern="^(buy|sell|adjustment)$")
    tradeDate: date
    unitPrice: int = Field(ge=1)
    quantity: int
    feeRate: Decimal = Field(default=Decimal("0"), ge=Decimal("0"), lt=Decimal("1"))
    memo: str | None = None


class ItemTradeCancelRequest(BaseModel):
    """자산 거래 취소 시 선택적으로 남기는 취소 사유입니다."""

    cancelReason: str | None = None


class ItemTradeRead(BaseModel):
    """자산 거래 그리드에 표시할 거래 원본값과 계산 결과를 함께 담습니다."""

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
    """자산별 재고관리 탭에서 보여줄 현재 재고와 누적 손익 요약입니다."""

    itemCodeId: int
    itemCode: str
    itemName: str
    inventoryQuantity: int
    inventoryValue: int
    averageBuyUnitPrice: int
    minimumProfitableUnitPrice: int
    totalProfitAmount: int


class ItemTradeListResponse(BaseModel):
    """자산 거래 목록, 자산별 요약, 페이지네이션 정보를 한 번에 내려줍니다."""

    items: list[ItemTradeRead]
    summaries: list[ItemCodeSummary]
    page: int
    size: int
    totalCount: int

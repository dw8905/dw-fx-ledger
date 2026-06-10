from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BuyLotCreateRequest(BaseModel):
    """FX 매수 등록 시 원화 금액과 적용 환율을 검증하는 요청 모델입니다."""

    buyDate: date
    buyKrwAmount: int = Field(gt=0)
    buyExchangeRate: Decimal = Field(gt=0)


class BuyLotUpdateRequest(BaseModel):
    """아직 매도에 쓰이지 않은 매수 로트를 수정할 때 받는 요청 모델입니다."""

    buyDate: date
    buyKrwAmount: int = Field(gt=0)
    buyExchangeRate: Decimal = Field(gt=0)


class BuyLotRead(BaseModel):
    """매수 로트 목록/상세 화면에 표시할 매수 로트 정보입니다."""

    buyLotId: int
    buyDate: date
    buyKrwAmount: int
    buyExchangeRate: Decimal
    usdAmount: Decimal
    lotStatus: str
    isActive: bool
    createdAt: datetime


class BuyLotListResponse(BaseModel):
    """매수 로트 목록과 페이지 정보를 함께 내려주는 응답 모델입니다."""

    items: list[BuyLotRead]
    page: int
    size: int
    totalCount: int


class ManualLotAllocationRequest(BaseModel):
    """수동 차감 전략에서 특정 매수 로트를 얼마만큼 쓸지 지정합니다."""

    buyLotId: int
    usdAmount: Decimal = Field(gt=0)


class SellTransactionCreateRequest(BaseModel):
    """FX 매도 등록 시 금액, 환율, 차감 전략, 수동 배분값을 검증합니다."""

    sellDate: date
    sellUsdAmount: Decimal = Field(gt=0)
    sellExchangeRate: Decimal = Field(gt=0)
    allocationStrategy: str | None = Field(default=None, pattern="^(highest_rate_first|fifo|lifo|manual)$")
    manualAllocations: list[ManualLotAllocationRequest] | None = None
    memo: str | None = None


class SellTransactionCancelRequest(BaseModel):
    """매도 취소 시 감사 로그에 남길 취소 사유를 받습니다."""

    cancelReason: str = Field(min_length=1, max_length=500)


class LotAllocationRead(BaseModel):
    """한 매도 거래가 한 매수 로트를 차감한 결과를 상세로 보여줍니다."""

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
    """매도 상세 화면에서 거래 합계와 로트별 차감 내역을 함께 담습니다."""

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
    """매도 목록 테이블 한 행에 필요한 매도 거래 요약입니다."""

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
    """매도 거래 목록과 페이지 정보를 함께 내려주는 응답 모델입니다."""

    items: list[SellTransactionListItem]
    page: int
    size: int
    totalCount: int


class LedgerRowRead(BaseModel):
    """FX 원장 그리드의 한 행이며 매수/매도/손익 계산 결과를 한 줄로 표현합니다."""

    buyDate: date
    buyKrwAmount: int
    buyExchangeRate: Decimal
    usdAmount: Decimal
    sellDate: date | None
    sellExchangeRate: Decimal | None
    sellKrwAmount: int | None
    profitKrw: int
    exchangeDiff: Decimal
    exchangeDiffAverage: Decimal | None
    cumulativeProfitKrw: int
    lotStatus: str
    buyLotId: int
    sellTransactionId: int | None
    lotAllocationId: int | None


class LedgerSummaryRead(BaseModel):
    """FX 원장 상단 카드에 표시할 전체/기간 기준 합계와 마지막 기준일입니다."""

    totalRows: int
    visibleRows: int
    openLotCount: int
    soldAllocationCount: int
    totalSellTransactionCount: int
    totalRealProfitKrw: int
    totalDisplayProfitKrw: int
    finalCumulativeProfitKrw: int
    latestLedgerDate: date | None


class LedgerResponse(BaseModel):
    """FX 원장 행 목록과 요약, 선택 기간을 함께 반환합니다."""

    items: list[LedgerRowRead]
    summary: LedgerSummaryRead
    period: str


class LotEventRead(BaseModel):
    """로트 생성/차감/복원 이벤트 로그를 관리자와 Dev Lab에서 읽는 형태입니다."""

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
    """FX 로트 이벤트 목록과 페이지 정보를 함께 내려주는 응답 모델입니다."""

    items: list[LotEventRead]
    page: int
    size: int
    totalCount: int

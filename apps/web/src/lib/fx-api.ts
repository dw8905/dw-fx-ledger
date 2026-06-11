import { apiFetch } from "./api";

export type CurrencyCode = "USD" | "JPY";

export const currencyOptions: Array<{ code: CurrencyCode; label: string; amountLabel: string; symbol: string }> = [
  { code: "USD", label: "USD 달러", amountLabel: "달러", symbol: "$" },
  { code: "JPY", label: "JPY 엔화", amountLabel: "엔화", symbol: "¥" }
];

export function getCurrencyOption(currencyCode: string) {
  /** 통화 코드에 맞는 화면 표시용 라벨과 기호를 반환합니다. */

  return currencyOptions.find((option) => option.code === currencyCode) ?? currencyOptions[0];
}

export type BuyLot = {
  /** 매수 로트 목록/상세에서 쓰는 FX 매수 원장 단위입니다. */
  buyLotId: number;
  currencyCode: CurrencyCode;
  quoteUnit: string;
  buyDate: string;
  buyKrwAmount: number;
  buyExchangeRate: string;
  usdAmount: string;
  lotStatus: string;
  isActive: boolean;
  createdAt: string;
};

export type BuyLotListResponse = {
  /** 매수 로트 목록과 페이지 정보를 담은 API 응답입니다. */
  items: BuyLot[];
  page: number;
  size: number;
  totalCount: number;
};

export type SellTransaction = {
  /** 매도 거래 상세와 목록에서 공통으로 쓰는 매도 거래 모델입니다. */
  sellTransactionId: number;
  currencyCode: CurrencyCode;
  quoteUnit: string;
  sellDate: string;
  sellUsdAmount: string;
  sellExchangeRate: string;
  allocationStrategy: string;
  transactionStatus: string;
  totalBuyKrwAmount: number;
  totalSellKrwAmount: number;
  totalRealProfitKrw: number;
  totalDisplayProfitKrw: number;
  memo: string | null;
  createdAt: string;
  allocations?: LotAllocation[];
};

export type LotAllocation = {
  /** 한 매도 거래가 특정 매수 로트를 얼마나 차감했는지 나타냅니다. */
  lotAllocationId: number;
  sourceBuyLotId: number;
  closedBuyLotId: number;
  remainingBuyLotId: number | null;
  allocatedUsdAmount: string;
  allocatedBuyKrwAmount: number;
  allocatedSellKrwAmount: number;
  realProfitKrw: number;
  displayProfitKrw: number;
  exchangeDiff: string;
};

export type LotEvent = {
  /** FX 로트 분리/복원 같은 감사 이벤트 로그 한 건입니다. */
  lotEventId: number;
  eventType: string;
  eventStatus: string;
  rootBuyLotId: number | null;
  sellTransactionId: number | null;
  lotAllocationId: number | null;
  sourceBuyLotId: number | null;
  closedBuyLotId: number | null;
  remainingBuyLotId: number | null;
  restoredBuyLotId: number | null;
  relatedEventId: number | null;
  eventPayload: Record<string, unknown> | null;
  createdAt: string;
};

export type LotEventListResponse = {
  /** FX 이벤트 로그 목록과 페이지 정보를 담은 API 응답입니다. */
  items: LotEvent[];
  page: number;
  size: number;
  totalCount: number;
};

export type SellTransactionListResponse = {
  /** 매도 거래 목록과 페이지 정보를 담은 API 응답입니다. */
  items: SellTransaction[];
  page: number;
  size: number;
  totalCount: number;
};

export type LedgerRow = {
  /** FX 원장 그리드와 통계 차트의 기준이 되는 한 행입니다. */
  buyDate: string;
  currencyCode: CurrencyCode;
  quoteUnit: string;
  buyKrwAmount: number;
  buyExchangeRate: string;
  usdAmount: string;
  sellDate: string | null;
  sellExchangeRate: string | null;
  sellKrwAmount: number | null;
  profitKrw: number;
  exchangeDiff: string;
  exchangeDiffAverage: string | null;
  cumulativeProfitKrw: number;
  lotStatus: string;
  buyLotId: number;
  sellTransactionId: number | null;
  lotAllocationId: number | null;
};

export type LedgerSummary = {
  /** FX 원장 상단 요약 카드와 통계 집계에 쓰는 합계 정보입니다. */
  totalRows: number;
  visibleRows: number;
  openLotCount: number;
  currencyCode: CurrencyCode;
  quoteUnit: string;
  totalOpenUsdAmount: string;
  soldAllocationCount: number;
  totalSellTransactionCount: number;
  totalRealProfitKrw: number;
  totalDisplayProfitKrw: number;
  finalCumulativeProfitKrw: number;
  latestLedgerDate: string | null;
};

export type LedgerResponse = {
  /** FX 원장 행 목록, 요약, 선택 기간을 함께 담은 응답입니다. */
  items: LedgerRow[];
  summary: LedgerSummary;
  period: string;
};

/** 테이블 정렬 방향을 오름차순, 내림차순, 정렬 없음으로 표현합니다. */
export type SortOrder = "asc" | "desc" | null;

export function formatAllocationStrategy(strategy: string) {
  /** 서버의 allocation_strategy 코드를 사람이 읽는 한국어 라벨로 바꿉니다. */

  if (strategy === "highest_rate_first") {
    return "환율 높은 순";
  }

  if (strategy === "fifo") {
    return "오래된 매수순";
  }

  if (strategy === "lifo") {
    return "최근 매수순";
  }

  if (strategy === "manual") {
    return "직접 선택";
  }

  return strategy;
}

function withSort(path: string, sortBy?: string | null, sortOrder?: SortOrder) {
  /** 정렬값이 있을 때만 API 경로에 sort_by/sort_order 쿼리를 붙입니다. */

  if (!sortBy || !sortOrder) {
    return path;
  }

  return `${path}&sort_by=${encodeURIComponent(sortBy)}&sort_order=${sortOrder}`;
}

export async function listBuyLots(
  page = 1,
  size = 10,
  sortBy?: string | null,
  sortOrder?: SortOrder,
  currencyCode: CurrencyCode = "USD"
) {
  /** 매수 로트 목록을 페이지와 정렬 조건으로 조회합니다. */

  return apiFetch<BuyLotListResponse>(
    withSort(`/fx/buy-lots?page=${page}&size=${size}&currencyCode=${currencyCode}`, sortBy, sortOrder)
  );
}

export async function listOpenBuyLotsForSelection(currencyCode: CurrencyCode = "USD") {
  /** 수동 매도 차감 화면에서 선택 가능한 open 로트를 환율 높은 순으로 가져옵니다. */

  return apiFetch<BuyLotListResponse>(
    `/fx/buy-lots?page=1&size=100&lot_status=open&is_active=true&sort_by=buy_exchange_rate&sort_order=desc&currencyCode=${currencyCode}`
  );
}

export async function getBuyLot(buyLotId: number) {
  /** 매수 로트 수정 화면에서 단일 로트 정보를 조회합니다. */

  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`);
}

export async function createBuyLot(input: {
  currencyCode: CurrencyCode;
  buyDate: string;
  buyKrwAmount: number;
  buyExchangeRate: string;
}) {
  /** 새 FX 매수 로트를 등록합니다. */

  return apiFetch<BuyLot>("/fx/buy-lots", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function updateBuyLot(
  buyLotId: number,
  input: {
    currencyCode: CurrencyCode;
    buyDate: string;
    buyKrwAmount: number;
    buyExchangeRate: string;
  }
) {
  /** 기존 FX 매수 로트의 날짜, 원화 금액, 환율을 수정합니다. */

  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`, {
    method: "PUT",
    body: JSON.stringify(input)
  });
}

export async function deleteBuyLot(buyLotId: number) {
  /** 아직 allocation 이력이 없는 매수 로트를 삭제 요청합니다. */

  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`, {
    method: "DELETE"
  });
}

export async function listSellTransactions(
  page = 1,
  size = 10,
  sortBy?: string | null,
  sortOrder?: SortOrder,
  currencyCode: CurrencyCode = "USD"
) {
  /** 매도 거래 목록을 페이지와 정렬 조건으로 조회합니다. */

  return apiFetch<SellTransactionListResponse>(
    withSort(`/fx/sell-transactions?page=${page}&size=${size}&currencyCode=${currencyCode}`, sortBy, sortOrder)
  );
}

export async function createSellTransaction(input: {
  currencyCode: CurrencyCode;
  sellDate: string;
  sellUsdAmount: string;
  sellExchangeRate: string;
  allocationStrategy: string;
  manualAllocations?: Array<{
    buyLotId: number;
    usdAmount: string;
  }>;
  memo?: string;
}) {
  /** 매도 거래를 등록하고 서버에서 로트 차감/allocation을 수행하게 합니다. */

  return apiFetch<SellTransaction>("/fx/sell-transactions", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getSellTransaction(sellTransactionId: number) {
  /** 매도 상세 화면에서 거래와 allocation 목록을 조회합니다. */

  return apiFetch<SellTransaction>(`/fx/sell-transactions/${sellTransactionId}`);
}

export async function cancelSellTransaction(sellTransactionId: number, cancelReason: string) {
  /** 매도 거래를 취소하고 서버에서 로트 복원 이벤트를 만들게 합니다. */

  return apiFetch<SellTransaction>(`/fx/sell-transactions/${sellTransactionId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ cancelReason })
  });
}

export async function listLotEvents(page = 1, size = 10, currencyCode: CurrencyCode = "USD") {
  /** FX Dev Lab에서 로트 이벤트 로그를 페이지 단위로 조회합니다. */

  return apiFetch<LotEventListResponse>(`/fx/lot-events?page=${page}&size=${size}&currencyCode=${currencyCode}`);
}

export async function getLedger(period = "all", currencyCode: CurrencyCode = "USD") {
  /** FX 원장과 통계 차트에서 사용할 기간별 원장 데이터를 조회합니다. */

  return apiFetch<LedgerResponse>(`/fx/ledger?period=${encodeURIComponent(period)}&currencyCode=${currencyCode}`);
}

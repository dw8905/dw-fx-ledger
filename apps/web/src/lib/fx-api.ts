import { apiFetch } from "./api";

export type BuyLot = {
  buyLotId: number;
  buyDate: string;
  buyKrwAmount: number;
  buyExchangeRate: string;
  usdAmount: string;
  lotStatus: string;
  isActive: boolean;
  createdAt: string;
};

export type BuyLotListResponse = {
  items: BuyLot[];
  page: number;
  size: number;
  totalCount: number;
};

export type SellTransaction = {
  sellTransactionId: number;
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
  items: LotEvent[];
  page: number;
  size: number;
  totalCount: number;
};

export type SellTransactionListResponse = {
  items: SellTransaction[];
  page: number;
  size: number;
  totalCount: number;
};

export type LedgerRow = {
  buyDate: string;
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
  totalRows: number;
  visibleRows: number;
  openLotCount: number;
  soldAllocationCount: number;
  totalSellTransactionCount: number;
  totalRealProfitKrw: number;
  totalDisplayProfitKrw: number;
  finalCumulativeProfitKrw: number;
  latestLedgerDate: string | null;
};

export type LedgerResponse = {
  items: LedgerRow[];
  summary: LedgerSummary;
  period: string;
};

export type SortOrder = "asc" | "desc" | null;

export function formatAllocationStrategy(strategy: string) {
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
  if (!sortBy || !sortOrder) {
    return path;
  }

  return `${path}&sort_by=${encodeURIComponent(sortBy)}&sort_order=${sortOrder}`;
}

export async function listBuyLots(
  page = 1,
  size = 20,
  sortBy?: string | null,
  sortOrder?: SortOrder
) {
  return apiFetch<BuyLotListResponse>(
    withSort(`/fx/buy-lots?page=${page}&size=${size}`, sortBy, sortOrder)
  );
}

export async function listOpenBuyLotsForSelection() {
  return apiFetch<BuyLotListResponse>(
    "/fx/buy-lots?page=1&size=100&lot_status=open&is_active=true&sort_by=buy_exchange_rate&sort_order=desc"
  );
}

export async function getBuyLot(buyLotId: number) {
  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`);
}

export async function createBuyLot(input: {
  buyDate: string;
  buyKrwAmount: number;
  buyExchangeRate: string;
}) {
  return apiFetch<BuyLot>("/fx/buy-lots", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function updateBuyLot(
  buyLotId: number,
  input: {
    buyDate: string;
    buyKrwAmount: number;
    buyExchangeRate: string;
  }
) {
  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`, {
    method: "PUT",
    body: JSON.stringify(input)
  });
}

export async function deleteBuyLot(buyLotId: number) {
  return apiFetch<BuyLot>(`/fx/buy-lots/${buyLotId}`, {
    method: "DELETE"
  });
}

export async function listSellTransactions(
  page = 1,
  size = 20,
  sortBy?: string | null,
  sortOrder?: SortOrder
) {
  return apiFetch<SellTransactionListResponse>(
    withSort(`/fx/sell-transactions?page=${page}&size=${size}`, sortBy, sortOrder)
  );
}

export async function createSellTransaction(input: {
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
  return apiFetch<SellTransaction>("/fx/sell-transactions", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function getSellTransaction(sellTransactionId: number) {
  return apiFetch<SellTransaction>(`/fx/sell-transactions/${sellTransactionId}`);
}

export async function cancelSellTransaction(sellTransactionId: number, cancelReason: string) {
  return apiFetch<SellTransaction>(`/fx/sell-transactions/${sellTransactionId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ cancelReason })
  });
}

export async function listLotEvents(page = 1, size = 50) {
  return apiFetch<LotEventListResponse>(`/fx/lot-events?page=${page}&size=${size}`);
}

export async function getLedger(period = "all") {
  return apiFetch<LedgerResponse>(`/fx/ledger?period=${encodeURIComponent(period)}`);
}

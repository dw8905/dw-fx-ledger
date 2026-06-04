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

export type SortOrder = "asc" | "desc" | null;

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

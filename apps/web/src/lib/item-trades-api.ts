import { apiFetch } from "./api";

export type ItemCode = {
  itemCodeId: number;
  itemCode: string;
  itemName: string;
  memo: string | null;
  createdAt: string;
};

export type ItemCodeSummary = {
  itemCodeId: number;
  itemCode: string;
  itemName: string;
  inventoryQuantity: number;
  inventoryValue: number;
  averageBuyUnitPrice: number;
  minimumProfitableUnitPrice: number;
  totalProfitAmount: number;
};

export type ItemTrade = {
  itemTradeId: number;
  itemCodeId: number | null;
  itemCode: string | null;
  itemName: string;
  tradeType: "buy" | "sell" | "adjustment";
  tradeStatus: "active" | "cancelled";
  tradeDate: string;
  unitPrice: number;
  quantity: number;
  feeRate: string;
  minimumProfitableUnitPrice: number;
  averageBuyUnitPrice: number | null;
  inventoryQuantityAfter: number | null;
  inventoryValueAfter: number | null;
  buyDate: string;
  buyUnitPrice: number;
  sellDate: string | null;
  sellUnitPrice: number | null;
  totalBuyAmount: number;
  totalSellAmount: number | null;
  feeAmount: number | null;
  netSellAmount: number | null;
  profitAmount: number | null;
  cancelledAt: string | null;
  cancelReason: string | null;
  memo: string | null;
  createdAt: string;
};

export type ItemTradeListResponse = {
  items: ItemTrade[];
  summaries: ItemCodeSummary[];
  page: number;
  size: number;
  totalCount: number;
};

export type ItemTradeInput = {
  itemCode: string;
  itemName: string;
  tradeType: "buy" | "sell" | "adjustment";
  tradeDate: string;
  unitPrice: number;
  quantity: number;
  feeRate: string;
  memo?: string;
};

export async function listItemCodes() {
  return apiFetch<{ items: ItemCode[] }>("/item-trades/item-codes");
}

export async function listItemTrades(page = 1, size = 10) {
  return apiFetch<ItemTradeListResponse>(`/item-trades?page=${page}&size=${size}`);
}

export async function createItemTrade(input: ItemTradeInput) {
  return apiFetch<ItemTrade>("/item-trades", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function cancelItemTrade(itemTradeId: number, cancelReason?: string) {
  return apiFetch<ItemTrade>(`/item-trades/${itemTradeId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ cancelReason: cancelReason || undefined })
  });
}

import { apiFetch } from "./api";

export type ItemCode = {
  /** 관리자가 등록한 전역 자산 마스터를 사용자 화면에서 읽는 형태입니다. */
  itemCodeId: number;
  itemCode: string;
  itemName: string;
  memo: string | null;
  createdAt: string;
};

export type ItemCodeSummary = {
  /** 자산별 재고관리 탭에서 현재 보유수량, 평균단가, 손익을 보여주는 요약입니다. */
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
  /** 매수/매도/재고조정 그리드에 표시되는 자산 거래 한 건입니다. */
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
  /** 자산 거래 목록과 자산별 재고 요약을 함께 담은 응답입니다. */
  items: ItemTrade[];
  summaries: ItemCodeSummary[];
  page: number;
  size: number;
  totalCount: number;
};

export type ItemTradeInput = {
  /** 자산 매수/매도/재고조정 등록 시 API로 보내는 입력값입니다. */
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
  /** 자산명 자동완성에 사용할 활성 자산 마스터 목록을 조회합니다. */

  return apiFetch<{ items: ItemCode[] }>("/item-trades/item-codes");
}

export async function listItemTrades(page = 1, size = 10) {
  /** 현재 사용자의 자산 거래 목록과 재고 요약을 페이지 단위로 조회합니다. */

  return apiFetch<ItemTradeListResponse>(`/item-trades?page=${page}&size=${size}`);
}

export async function createItemTrade(input: ItemTradeInput) {
  /** 자산 매수, 매도, 재고조정 거래를 등록합니다. */

  return apiFetch<ItemTrade>("/item-trades", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export async function cancelItemTrade(itemTradeId: number, cancelReason?: string) {
  /** 자산 거래를 삭제하지 않고 취소 상태로 전환하도록 요청합니다. */

  return apiFetch<ItemTrade>(`/item-trades/${itemTradeId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ cancelReason: cancelReason || undefined })
  });
}

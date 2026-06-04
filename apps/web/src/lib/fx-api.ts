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

export async function listBuyLots(page = 1, size = 20) {
  return apiFetch<BuyLotListResponse>(`/fx/buy-lots?page=${page}&size=${size}`);
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

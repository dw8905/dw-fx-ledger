import { apiFetch } from "./api";

export type AdminUserListItem = {
  user_id: number;
  email: string;
  login_id: string | null;
  display_name: string;
  user_status: string;
  roles: string[];
  created_at: string;
};

export type AdminUserDetail = AdminUserListItem & {
  default_allocation_strategy: string;
  updated_at: string;
  fx_summary: {
    buy_lot_count: number;
    open_lot_count: number;
    sell_transaction_count: number;
    lot_event_count: number;
    total_real_profit_krw: number;
    total_display_profit_krw: number;
    open_usd_amount: string;
  };
};

export type Paginated<T> = {
  items: T[];
  page: number;
  size: number;
  total_count: number;
};

export type AdminPost = {
  post_id: number;
  author_id: number;
  author_name: string;
  title: string;
  view_count: number;
  post_status: string;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
};

export type LedgerResponse = {
  items: Array<{
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
  }>;
  summary: {
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
  period: string;
};

export type AdminUserLedger = {
  user: AdminUserListItem;
  ledger: LedgerResponse;
};

export type AdminLotEvent = {
  lot_event_id: number;
  user_id: number;
  event_type: string;
  event_status: string;
  root_buy_lot_id: number | null;
  sell_transaction_id: number | null;
  lot_allocation_id: number | null;
  source_buy_lot_id: number | null;
  closed_buy_lot_id: number | null;
  remaining_buy_lot_id: number | null;
  restored_buy_lot_id: number | null;
  related_event_id: number | null;
  event_payload: Record<string, unknown> | null;
  created_at: string;
};

export function listUsers(page = 1, size = 20) {
  return apiFetch<Paginated<AdminUserListItem>>(`/admin/users?page=${page}&size=${size}`);
}

export function getUser(userId: number) {
  return apiFetch<AdminUserDetail>(`/admin/users/${userId}`);
}

export function listPosts(options: { includeDeleted?: boolean } = {}) {
  const includeDeleted = options.includeDeleted ? "true" : "false";
  return apiFetch<Paginated<AdminPost>>(`/admin/posts?include_deleted=${includeDeleted}`);
}

export function getUserLedger(userId: number, period: string) {
  return apiFetch<AdminUserLedger>(`/admin/fx/users/${userId}/ledger?period=${period}`);
}

export function listLotEvents(options: { userId?: string; eventType?: string } = {}) {
  const params = new URLSearchParams();
  if (options.userId) {
    params.set("user_id", options.userId);
  }
  if (options.eventType) {
    params.set("event_type", options.eventType);
  }
  const query = params.toString();
  return apiFetch<Paginated<AdminLotEvent>>(`/admin/fx/lot-events${query ? `?${query}` : ""}`);
}

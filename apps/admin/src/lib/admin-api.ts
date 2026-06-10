import { apiFetch } from "./api";

export type AdminUserListItem = {
  /** 관리자 사용자 목록과 사용자 선택 UI에서 쓰는 계정 요약입니다. */
  user_id: number;
  email: string;
  login_id: string | null;
  display_name: string;
  user_status: string;
  roles: string[];
  created_at: string;
};

export type AdminUserDetail = AdminUserListItem & {
  /** 관리자 사용자 상세 화면에서 기본 계정 정보에 FX 요약을 더한 모델입니다. */
  default_allocation_strategy: string;
  updated_at: string;
  fx_summary: {
    total_buy_krw_amount: number;
    total_buy_usd_amount: string;
    buy_lot_count: number;
    open_lot_count: number;
    sell_transaction_count: number;
    lot_event_count: number;
    total_real_profit_krw: number;
    total_display_profit_krw: number;
    final_cumulative_profit_krw: number;
    latest_ledger_date: string | null;
    open_usd_amount: string;
  };
};

export type Paginated<T> = {
  /** 관리자 목록 API들이 공통으로 반환하는 페이지네이션 래퍼입니다. */
  items: T[];
  page: number;
  size: number;
  total_count: number;
  total_pages: number;
};

export type AdminPost = {
  /** 관리자 게시글 목록에서 삭제 여부까지 함께 보여주는 게시글 모델입니다. */
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
  /** 관리자에서 특정 사용자의 FX 원장을 조회할 때 받는 원장 응답입니다. */
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
  /** 조회 대상 사용자 정보와 그 사용자의 FX 원장을 함께 담습니다. */
  user: AdminUserListItem;
  ledger: LedgerResponse;
};

export type AdminLotEvent = {
  /** 관리자 FX 이벤트 로그 화면에 표시되는 로트 이벤트 모델입니다. */
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

export type AdminItemCode = {
  /** 관리자 자산 마스터 관리 화면에서 쓰는 자산 코드 모델입니다. */
  item_code_id: number;
  item_code: string;
  item_name: string;
  memo: string | null;
  is_active: boolean;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
};

export function listUsers(options: {
  page?: number;
  size?: number;
  keyword?: string;
  userStatus?: string;
  role?: string;
} = {}) {
  /** 관리자 사용자 목록을 검색어, 상태, role, 페이지 조건으로 조회합니다. */

  const params = new URLSearchParams();
  params.set("page", String(options.page ?? 1));
  params.set("size", String(options.size ?? 10));
  if (options.keyword) {
    params.set("keyword", options.keyword);
  }
  if (options.userStatus) {
    params.set("user_status", options.userStatus);
  }
  if (options.role) {
    params.set("role", options.role);
  }
  return apiFetch<Paginated<AdminUserListItem>>(`/admin/users?${params}`);
}

export function getUser(userId: number) {
  /** 관리자 사용자 상세 화면에서 특정 사용자 정보를 조회합니다. */

  return apiFetch<AdminUserDetail>(`/admin/users/${userId}`);
}

export function listPosts(options: {
  page?: number;
  size?: number;
  includeDeleted?: boolean;
  keyword?: string;
  postStatus?: string;
} = {}) {
  /** 관리자 게시글 목록을 검색어, 상태, 삭제글 포함 여부로 조회합니다. */

  const params = new URLSearchParams();
  params.set("page", String(options.page ?? 1));
  params.set("size", String(options.size ?? 10));
  params.set("include_deleted", options.includeDeleted ? "true" : "false");
  if (options.keyword) {
    params.set("keyword", options.keyword);
  }
  if (options.postStatus) {
    params.set("post_status", options.postStatus);
  }
  return apiFetch<Paginated<AdminPost>>(`/admin/posts?${params}`);
}

export function getUserLedger(userId: number, period: string) {
  /** 특정 사용자의 FX 원장을 선택 기간 기준으로 조회합니다. */

  return apiFetch<AdminUserLedger>(`/admin/fx/users/${userId}/ledger?period=${period}`);
}

export function listLotEvents(options: {
  page?: number;
  size?: number;
  userId?: string;
  eventType?: string;
  sellTransactionId?: string;
  rootBuyLotId?: string;
} = {}) {
  /** 관리자 FX 이벤트 로그를 사용자/이벤트/거래/루트 로트 조건으로 조회합니다. */

  const params = new URLSearchParams();
  params.set("page", String(options.page ?? 1));
  params.set("size", String(options.size ?? 10));
  if (options.userId) {
    params.set("user_id", options.userId);
  }
  if (options.eventType) {
    params.set("event_type", options.eventType);
  }
  if (options.sellTransactionId) {
    params.set("sell_transaction_id", options.sellTransactionId);
  }
  if (options.rootBuyLotId) {
    params.set("root_buy_lot_id", options.rootBuyLotId);
  }
  return apiFetch<Paginated<AdminLotEvent>>(`/admin/fx/lot-events?${params}`);
}

export function listItemCodes(options: {
  page?: number;
  size?: number;
  keyword?: string;
  isActive?: string;
} = {}) {
  /** 관리자 자산 마스터 목록을 검색어와 활성 상태 기준으로 조회합니다. */

  const params = new URLSearchParams();
  params.set("page", String(options.page ?? 1));
  params.set("size", String(options.size ?? 10));
  if (options.keyword) {
    params.set("keyword", options.keyword);
  }
  if (options.isActive) {
    params.set("is_active", options.isActive);
  }
  return apiFetch<Paginated<AdminItemCode>>(`/admin/item-codes?${params}`);
}

export function createItemCode(input: {
  item_name: string;
  memo?: string;
  is_active: boolean;
}) {
  /** 관리자에서 새 자산 마스터를 생성합니다. 내부 코드는 서버가 자동 생성합니다. */

  return apiFetch<AdminItemCode>("/admin/item-codes", {
    method: "POST",
    body: JSON.stringify(input)
  });
}

export function updateItemCode(
  itemCodeId: number,
  input: {
    item_name: string;
    memo?: string;
    is_active: boolean;
  }
) {
  /** 관리자에서 기존 자산 마스터의 이름, 메모, 활성 상태를 수정합니다. */

  return apiFetch<AdminItemCode>(`/admin/item-codes/${itemCodeId}`, {
    method: "PUT",
    body: JSON.stringify(input)
  });
}

export function deactivateItemCode(itemCodeId: number) {
  /** 자산 마스터를 삭제하지 않고 비활성 상태로 전환합니다. */

  return apiFetch<AdminItemCode>(`/admin/item-codes/${itemCodeId}`, {
    method: "DELETE"
  });
}

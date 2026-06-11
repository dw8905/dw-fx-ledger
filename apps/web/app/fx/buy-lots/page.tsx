"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { SortableHeader, type SortOrder } from "../../../src/components/sortable-header";
import { formatDate, formatDateTime, formatDecimal, formatForeignCurrency, formatKrw } from "../../../src/lib/format";
import {
  currencyOptions,
  deleteBuyLot,
  getCurrencyOption,
  listBuyLots,
  type BuyLotListResponse,
  type CurrencyCode
} from "../../../src/lib/fx-api";

function BuyLotsContent() {
  /** 매수 로트 목록의 정렬 상태와 삭제 요청 흐름을 관리합니다. */

  const [data, setData] = useState<BuyLotListResponse | null>(null);
  const [error, setError] = useState("");
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>("USD");
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);
  const [deletingBuyLotId, setDeletingBuyLotId] = useState<number | null>(null);

  function handleSort(field: string) {
    /** 같은 헤더를 반복 클릭하면 asc, desc, 정렬 해제 순서로 전환합니다. */

    if (sortBy !== field) {
      setSortBy(field);
      setSortOrder("asc");
      return;
    }

    if (sortOrder === "asc") {
      setSortOrder("desc");
      return;
    }

    setSortBy(null);
    setSortOrder(null);
  }

  const loadBuyLots = useCallback(() => {
    /** 현재 정렬 조건으로 첫 페이지 매수 로트를 다시 불러옵니다. */

    listBuyLots(1, 20, sortBy, sortOrder, currencyCode)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매수 로트를 불러오지 못했습니다.")
      );
  }, [sortBy, sortOrder, currencyCode]);

  const selectedCurrency = getCurrencyOption(currencyCode);

  useEffect(() => {
    loadBuyLots();
  }, [loadBuyLots]);

  async function handleDelete(buyLotId: number) {
    /** 삭제 확인 후 open 매수 로트 삭제 API를 호출하고 목록을 새로고침합니다. */

    if (!window.confirm("이 매수 로트를 삭제할까요? 삭제 후 기본 목록에서 제외됩니다.")) {
      return;
    }

    setError("");
    setDeletingBuyLotId(buyLotId);
    try {
      await deleteBuyLot(buyLotId);
      await loadBuyLots();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매수 로트 삭제에 실패했습니다.");
    } finally {
      setDeletingBuyLotId(null);
    }
  }

  return (
    <main className="content-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Ledger</p>
          <h1>매수 로트 목록</h1>
        </div>
        <Link className="primary-link" href="/fx/buy-lots/new">
          매수 등록
        </Link>
      </section>
      <section className="filter-bar">
        <label>
          통화
          <select value={currencyCode} onChange={(event) => setCurrencyCode(event.target.value as CurrencyCode)}>
            {currencyOptions.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <p className="form-error">{error}</p> : null}
      {!data ? (
        <p>매수 로트를 불러오는 중입니다.</p>
      ) : (
        <div className="table-wrap">
          <table className="post-table">
            <thead>
              <tr>
                <th>번호</th>
                <th>
                  <SortableHeader label="매수일" field="buy_date" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="매수원화환전금액" field="buy_krw_amount" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="매수적용환율" field="buy_exchange_rate" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label={`${selectedCurrency.amountLabel}환전금액`} field="usd_amount" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="상태" field="lot_status" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="등록일" field="created_at" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {data.items.length === 0 ? (
                <tr>
                  <td colSpan={8}>매수 로트가 없습니다.</td>
                </tr>
              ) : (
                data.items.map((lot) => (
                  <tr key={lot.buyLotId}>
                    <td>{lot.buyLotId}</td>
                    <td>{formatDate(lot.buyDate)}</td>
                    <td>{formatKrw(lot.buyKrwAmount)} KRW</td>
                    <td>{formatDecimal(lot.buyExchangeRate)}</td>
                    <td>{formatForeignCurrency(lot.usdAmount, lot.currencyCode)}</td>
                    <td>{lot.lotStatus}</td>
                    <td>{formatDateTime(lot.createdAt)}</td>
                    <td>
                      {lot.lotStatus === "open" && lot.isActive ? (
                        <div className="table-actions">
                          <Link href={`/fx/buy-lots/${lot.buyLotId}/edit`}>수정</Link>
                          <button
                            className="link-button danger-link"
                            disabled={deletingBuyLotId === lot.buyLotId}
                            type="button"
                            onClick={() => void handleDelete(lot.buyLotId)}
                          >
                            {deletingBuyLotId === lot.buyLotId ? "삭제 중" : "삭제"}
                          </button>
                        </div>
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          <p className="pagination-summary">
            page {data.page} / size {data.size} / total {data.totalCount}
          </p>
        </div>
      )}
    </main>
  );
}

export default function BuyLotsPage() {
  /** 매수 로트 목록 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <BuyLotsContent />
    </AuthGuard>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { SortableHeader, type SortOrder } from "../../../src/components/sortable-header";
import { formatDate, formatDateTime, formatDecimal, formatKrw } from "../../../src/lib/format";
import { listBuyLots, type BuyLotListResponse } from "../../../src/lib/fx-api";

function BuyLotsContent() {
  const [data, setData] = useState<BuyLotListResponse | null>(null);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);

  function handleSort(field: string) {
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

  useEffect(() => {
    listBuyLots(1, 20, sortBy, sortOrder)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매수 로트를 불러오지 못했습니다.")
      );
  }, [sortBy, sortOrder]);

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
                  <SortableHeader label="달러환전금액" field="usd_amount" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
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
                    <td>{formatDecimal(lot.usdAmount)} USD</td>
                    <td>{lot.lotStatus}</td>
                    <td>{formatDateTime(lot.createdAt)}</td>
                    <td>
                      {lot.lotStatus === "open" && lot.isActive ? (
                        <Link href={`/fx/buy-lots/${lot.buyLotId}/edit`}>수정</Link>
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
  return (
    <AuthGuard>
      <BuyLotsContent />
    </AuthGuard>
  );
}

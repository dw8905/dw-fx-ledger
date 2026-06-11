"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { SortableHeader, type SortOrder } from "../../../src/components/sortable-header";
import { formatDate, formatDecimal, formatForeignCurrency, formatKrw } from "../../../src/lib/format";
import {
  currencyOptions,
  formatAllocationStrategy,
  getCurrencyOption,
  listSellTransactions,
  type CurrencyCode,
  type SellTransactionListResponse
} from "../../../src/lib/fx-api";

function SellTransactionsContent() {
  /** 매도 거래 목록의 정렬 상태를 관리하고 거래 요약을 표시합니다. */

  const [data, setData] = useState<SellTransactionListResponse | null>(null);
  const [error, setError] = useState("");
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>("USD");
  const [sortBy, setSortBy] = useState<string | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);

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

  useEffect(() => {
    listSellTransactions(1, 10, sortBy, sortOrder, currencyCode)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매도 거래를 불러오지 못했습니다.")
      );
  }, [sortBy, sortOrder, currencyCode]);

  const selectedCurrency = getCurrencyOption(currencyCode);

  return (
    <main className="content-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Ledger</p>
          <h1>매도 거래 목록</h1>
        </div>
        <Link className="primary-link" href="/fx/sell-transactions/new">
          매도 등록
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
        <p>매도 거래를 불러오는 중입니다.</p>
      ) : (
        <div className="table-wrap">
          <table className="post-table">
            <thead>
              <tr>
                <th>번호</th>
                <th>
                  <SortableHeader label="매도일" field="sell_date" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label={`매도 ${selectedCurrency.amountLabel}`} field="sell_usd_amount" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="매도환율" field="sell_exchange_rate" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>전략</th>
                <th>
                  <SortableHeader label="상태" field="transaction_status" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="실제손익" field="total_real_profit_krw" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
                <th>
                  <SortableHeader label="표시손익" field="total_display_profit_krw" sortBy={sortBy} sortOrder={sortOrder} onSort={handleSort} />
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.length === 0 ? (
                <tr>
                  <td colSpan={8}>매도 거래가 없습니다.</td>
                </tr>
              ) : (
                data.items.map((transaction) => (
                  <tr key={transaction.sellTransactionId}>
                    <td>
                      <Link href={`/fx/sell-transactions/${transaction.sellTransactionId}`}>
                        {transaction.sellTransactionId}
                      </Link>
                    </td>
                    <td>{formatDate(transaction.sellDate)}</td>
                    <td>{formatForeignCurrency(transaction.sellUsdAmount, transaction.currencyCode)}</td>
                    <td>{formatDecimal(transaction.sellExchangeRate)}</td>
                    <td>{formatAllocationStrategy(transaction.allocationStrategy)}</td>
                    <td>{transaction.transactionStatus}</td>
                    <td>{formatKrw(transaction.totalRealProfitKrw)} KRW</td>
                    <td>{formatKrw(transaction.totalDisplayProfitKrw)} KRW</td>
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

export default function SellTransactionsPage() {
  /** 매도 거래 목록 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <SellTransactionsContent />
    </AuthGuard>
  );
}

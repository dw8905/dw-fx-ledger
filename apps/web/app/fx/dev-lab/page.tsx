"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { formatDate, formatDateTime, formatDecimal, formatKrw } from "../../../src/lib/format";
import {
  listLotEvents,
  listSellTransactions,
  type LotEventListResponse,
  type SellTransactionListResponse
} from "../../../src/lib/fx-api";

function DevLabContent() {
  const [transactions, setTransactions] = useState<SellTransactionListResponse | null>(null);
  const [events, setEvents] = useState<LotEventListResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([listSellTransactions(1, 10), listLotEvents(1, 30)])
      .then(([transactionData, eventData]) => {
        setTransactions(transactionData);
        setEvents(eventData);
      })
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "FX 개발 데이터를 불러오지 못했습니다.")
      );
  }, []);

  return (
    <main className="content-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Ledger</p>
          <h1>FX Dev Lab</h1>
        </div>
        <div className="button-row">
          <Link className="secondary-link" href="/fx/buy-lots">
            매수 로트
          </Link>
          <Link className="primary-link" href="/fx/sell-transactions/new">
            매도 등록
          </Link>
        </div>
      </section>

      {error ? <p className="form-error">{error}</p> : null}

      <section className="detail-panel">
        <h2>최근 매도 거래</h2>
        {!transactions ? (
          <p>매도 거래를 불러오는 중입니다.</p>
        ) : (
          <div className="table-wrap">
            <table className="post-table">
              <thead>
                <tr>
                  <th>번호</th>
                  <th>상태</th>
                  <th>매도일</th>
                  <th>USD</th>
                  <th>환율</th>
                  <th>실제손익</th>
                  <th>등록일</th>
                </tr>
              </thead>
              <tbody>
                {transactions.items.map((transaction) => (
                  <tr key={transaction.sellTransactionId}>
                    <td>
                      <Link href={`/fx/sell-transactions/${transaction.sellTransactionId}`}>
                        {transaction.sellTransactionId}
                      </Link>
                    </td>
                    <td>{transaction.transactionStatus}</td>
                    <td>{formatDate(transaction.sellDate)}</td>
                    <td>{formatDecimal(transaction.sellUsdAmount)} USD</td>
                    <td>{formatDecimal(transaction.sellExchangeRate)}</td>
                    <td>{formatKrw(transaction.totalRealProfitKrw)} KRW</td>
                    <td>{formatDateTime(transaction.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="detail-panel">
        <h2>최근 로트 이벤트</h2>
        {!events ? (
          <p>로트 이벤트를 불러오는 중입니다.</p>
        ) : (
          <div className="table-wrap">
            <table className="post-table">
              <thead>
                <tr>
                  <th>이벤트</th>
                  <th>유형</th>
                  <th>Root</th>
                  <th>매도</th>
                  <th>Source</th>
                  <th>Sold</th>
                  <th>Remaining</th>
                  <th>Restored</th>
                  <th>생성일</th>
                </tr>
              </thead>
              <tbody>
                {events.items.map((event) => (
                  <tr key={event.lotEventId}>
                    <td>{event.lotEventId}</td>
                    <td>{event.eventType}</td>
                    <td>{event.rootBuyLotId || "-"}</td>
                    <td>{event.sellTransactionId || "-"}</td>
                    <td>{event.sourceBuyLotId || "-"}</td>
                    <td>{event.closedBuyLotId || "-"}</td>
                    <td>{event.remainingBuyLotId || "-"}</td>
                    <td>{event.restoredBuyLotId || "-"}</td>
                    <td>{formatDateTime(event.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}

export default function FxDevLabPage() {
  return (
    <AuthGuard>
      <DevLabContent />
    </AuthGuard>
  );
}

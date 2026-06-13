"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import { Pagination } from "../../../src/components/pagination";
import { formatDate, formatDateTime, formatDecimal, formatForeignCurrency, formatKrw } from "../../../src/lib/format";
import {
  currencyOptions,
  getCurrencyOption,
  listLotEvents,
  listSellTransactions,
  type CurrencyCode,
  type LotEventListResponse,
  type SellTransactionListResponse
} from "../../../src/lib/fx-api";

function DevLabContent() {
  /** 개발/검증용으로 최근 매도 거래와 로트 이벤트를 각각 페이지네이션해 보여줍니다. */

  const [transactions, setTransactions] = useState<SellTransactionListResponse | null>(null);
  const [events, setEvents] = useState<LotEventListResponse | null>(null);
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>("USD");
  const [transactionPage, setTransactionPage] = useState(1);
  const [transactionSize, setTransactionSize] = useState(10);
  const [eventPage, setEventPage] = useState(1);
  const [eventSize, setEventSize] = useState(10);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listSellTransactions(transactionPage, transactionSize, null, null, currencyCode)
      .then(setTransactions)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매도 거래를 불러오지 못했습니다.")
      );
  }, [currencyCode, transactionPage, transactionSize]);

  useEffect(() => {
    setError("");
    listLotEvents(eventPage, eventSize, currencyCode)
      .then(setEvents)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "로트 이벤트를 불러오지 못했습니다.")
      );
  }, [currencyCode, eventPage, eventSize]);

  const selectedCurrency = getCurrencyOption(currencyCode);

  return (
    <main className="content-page">
      <section className="content-header content-header-actions">
        <div className="button-row">
          <Link className="secondary-link" href="/fx/buy-lots">
            매수 로트
          </Link>
          <Link className="primary-link" href="/fx/sell-transactions/new">
            매도 등록
          </Link>
        </div>
      </section>
      <section className="filter-bar">
        <label>
          통화
          <select
            value={currencyCode}
            onChange={(event) => {
              setCurrencyCode(event.target.value as CurrencyCode);
              setTransactionPage(1);
              setEventPage(1);
            }}
          >
            {currencyOptions.map((option) => (
              <option key={option.code} value={option.code}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </section>

      {error ? <p className="form-error">{error}</p> : null}

      <section className="detail-panel">
        <h2>최근 매도 거래</h2>
        {!transactions ? (
          <p>매도 거래를 불러오는 중입니다.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>번호</th>
                    <th>상태</th>
                    <th>매도일</th>
                    <th>{selectedCurrency.amountLabel}</th>
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
                      <td>{formatForeignCurrency(transaction.sellUsdAmount, transaction.currencyCode)}</td>
                      <td>{formatDecimal(transaction.sellExchangeRate)}</td>
                      <td>{formatKrw(transaction.totalRealProfitKrw)} KRW</td>
                      <td>{formatDateTime(transaction.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={transactions.page}
              size={transactions.size}
              totalCount={transactions.totalCount}
              onPageChange={setTransactionPage}
              onSizeChange={(nextSize) => {
                setTransactionSize(nextSize);
                setTransactionPage(1);
              }}
            />
          </>
        )}
      </section>

      <section className="detail-panel">
        <h2>최근 로트 이벤트</h2>
        {!events ? (
          <p>로트 이벤트를 불러오는 중입니다.</p>
        ) : (
          <>
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
            <Pagination
              page={events.page}
              size={events.size}
              totalCount={events.totalCount}
              onPageChange={setEventPage}
              onSizeChange={(nextSize) => {
                setEventSize(nextSize);
                setEventPage(1);
              }}
            />
          </>
        )}
      </section>
    </main>
  );
}

export default function FxDevLabPage() {
  /** FX Dev Lab 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <DevLabContent />
    </AuthGuard>
  );
}

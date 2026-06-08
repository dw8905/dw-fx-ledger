"use client";

import { useEffect, useState } from "react";
import { AuthGuard } from "../../../src/components/auth-guard";
import {
  formatCompactDate,
  formatKrw,
  formatKrwCurrency,
  formatKrwRate,
  formatUsdCurrency
} from "../../../src/lib/format";
import { getLedger, type LedgerResponse } from "../../../src/lib/fx-api";

const periodOptions = [
  { value: "all", label: "전체" },
  { value: "1y", label: "최근 1년" },
  { value: "3y", label: "최근 3년" },
  { value: "5y", label: "최근 5년" },
  { value: "latest", label: "마지막 날짜만" }
];

function formatNullableDate(value: string | null) {
  return value ? formatCompactDate(value) : "";
}

function formatNullableKrwRate(value: string | null) {
  return value ? formatKrwRate(value) : "";
}

function formatNullableKrw(value: number | null) {
  return value === null ? "" : formatKrwCurrency(value);
}

function escapeCsvCell(value: string | number | null) {
  const text = value === null ? "" : String(value);
  return `"${text.replaceAll("\"", "\"\"")}"`;
}

function buildLedgerCsv(data: LedgerResponse) {
  const headers = [
    "매수일",
    "매수원화환전금액",
    "매수적용환율",
    "달러환전금액",
    "매도일",
    "매도적용환율",
    "매도원화환전금액",
    "차익",
    "환율차",
    "환율차이평균"
  ];
  const rows = data.items.map((row) => [
    formatCompactDate(row.buyDate),
    formatKrwCurrency(row.buyKrwAmount),
    formatKrwRate(row.buyExchangeRate),
    formatUsdCurrency(row.usdAmount),
    formatNullableDate(row.sellDate),
    formatNullableKrwRate(row.sellExchangeRate),
    formatNullableKrw(row.sellKrwAmount),
    formatKrwCurrency(row.profitKrw),
    formatKrwRate(row.exchangeDiff),
    formatNullableKrwRate(row.exchangeDiffAverage)
  ]);

  return [headers, ...rows].map((row) => row.map(escapeCsvCell).join(",")).join("\r\n");
}

function downloadCsv(filename: string, csv: string) {
  const blob = new Blob([`\uFEFF${csv}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function getCsvFilename(period: string) {
  const timestamp = new Intl.DateTimeFormat("sv-SE", {
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    second: "2-digit",
    timeZone: "Asia/Seoul",
    year: "numeric"
  })
    .format(new Date())
    .replaceAll(" ", "_")
    .replaceAll(":", "");
  return `fx-ledger-${period}-${timestamp}.csv`;
}

function LedgerContent() {
  const [period, setPeriod] = useState("all");
  const [data, setData] = useState<LedgerResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    getLedger(period)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "원장을 불러오지 못했습니다.")
      );
  }, [period]);

  function handleCsvDownload() {
    if (!data || data.items.length === 0) {
      return;
    }

    downloadCsv(getCsvFilename(data.period), buildLedgerCsv(data));
  }

  return (
    <main className="content-page ledger-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Ledger</p>
          <h1>FX 원장</h1>
        </div>
        <div className="ledger-actions">
          <label className="period-select">
            기간 보기
            <select value={period} onChange={(event) => setPeriod(event.target.value)}>
              {periodOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="secondary-button"
            disabled={!data || data.items.length === 0}
            type="button"
            onClick={handleCsvDownload}
          >
            CSV 추출
          </button>
        </div>
      </section>

      {error ? <p className="form-error">{error}</p> : null}
      {!data ? (
        <p>원장을 불러오는 중입니다.</p>
      ) : (
        <>
          <section className="ledger-summary">
            <div>
              <span>전체 행</span>
              <strong>{formatKrw(data.summary.totalRows)}</strong>
            </div>
            <div>
              <span>표시 행</span>
              <strong>{formatKrw(data.summary.visibleRows)}</strong>
            </div>
            <div>
              <span>Open 로트</span>
              <strong>{formatKrw(data.summary.openLotCount)}</strong>
            </div>
            <div>
              <span>매도 Allocation</span>
              <strong>{formatKrw(data.summary.soldAllocationCount)}</strong>
            </div>
            <div>
              <span>매도 거래</span>
              <strong>{formatKrw(data.summary.totalSellTransactionCount)}</strong>
            </div>
            <div>
              <span>표시손익 합계</span>
              <strong>{formatKrwCurrency(data.summary.totalDisplayProfitKrw)}</strong>
            </div>
            <div>
              <span>최종 누적수익</span>
              <strong className="profit-strong">{formatKrwCurrency(data.summary.finalCumulativeProfitKrw)}</strong>
            </div>
            <div>
              <span>마지막 기준일</span>
              <strong>{data.summary.latestLedgerDate ? formatCompactDate(data.summary.latestLedgerDate) : ""}</strong>
            </div>
          </section>

          <div className="ledger-table-wrap">
            <table className="ledger-table">
              <thead>
                <tr>
                  <th>매수일</th>
                  <th>매수원화환전금액</th>
                  <th>매수적용환율</th>
                  <th>달러환전금액</th>
                  <th className="calc-col">매도일</th>
                  <th className="calc-col">매도적용환율</th>
                  <th className="calc-col">매도원화환전금액</th>
                  <th className="calc-col">차익</th>
                  <th className="calc-col">환율차</th>
                  <th className="calc-col">환율차이평균</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((row) => (
                  <tr key={`${row.buyLotId}-${row.lotAllocationId || "open"}`}>
                    <td>{formatCompactDate(row.buyDate)}</td>
                    <td className="numeric">{formatKrwCurrency(row.buyKrwAmount)}</td>
                    <td className="numeric">{formatKrwRate(row.buyExchangeRate)}</td>
                    <td className="numeric">{formatUsdCurrency(row.usdAmount)}</td>
                    <td className="calc-col">{formatNullableDate(row.sellDate)}</td>
                    <td className="calc-col numeric">{formatNullableKrwRate(row.sellExchangeRate)}</td>
                    <td className="calc-col numeric">{formatNullableKrw(row.sellKrwAmount)}</td>
                    <td className="calc-col numeric">{formatKrwCurrency(row.profitKrw)}</td>
                    <td className="calc-col numeric">{formatKrwRate(row.exchangeDiff)}</td>
                    <td className="calc-col numeric">{formatNullableKrwRate(row.exchangeDiffAverage)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}

export default function LedgerPage() {
  return (
    <AuthGuard>
      <LedgerContent />
    </AuthGuard>
  );
}

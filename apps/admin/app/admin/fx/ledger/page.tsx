"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AdminGuard } from "../../../../src/components/admin-guard";
import { AdminShell } from "../../../../src/components/admin-shell";
import { getUserLedger, type AdminUserLedger } from "../../../../src/lib/admin-api";
import { formatDate, formatKrw, formatNumber, formatUsd } from "../../../../src/lib/format";

const periodOptions = ["all", "1y", "3y", "5y", "latest"];

function LedgerContent() {
  const searchParams = useSearchParams();
  const initialUserId = searchParams.get("userId") ?? "";
  const [userIdInput, setUserIdInput] = useState(initialUserId);
  const [activeUserId, setActiveUserId] = useState(initialUserId);
  const [period, setPeriod] = useState("all");
  const [data, setData] = useState<AdminUserLedger | null>(null);
  const [error, setError] = useState("");

  const numericUserId = useMemo(() => Number(activeUserId), [activeUserId]);

  useEffect(() => {
    if (!Number.isFinite(numericUserId) || numericUserId <= 0) {
      setData(null);
      return;
    }

    setError("");
    getUserLedger(numericUserId, period)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "원장을 불러오지 못했습니다.")
      );
  }, [numericUserId, period]);

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">FX Ledger</p>
            <h1>사용자 FX 원장</h1>
          </div>
          <form
            className="inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              setActiveUserId(userIdInput);
            }}
          >
            <label>
              user_id
              <input value={userIdInput} onChange={(event) => setUserIdInput(event.target.value)} />
            </label>
            <label>
              기간
              <select value={period} onChange={(event) => setPeriod(event.target.value)}>
                {periodOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary-button" type="submit">
              조회
            </button>
          </form>
        </section>
        {error ? <p className="form-error">{error}</p> : null}
        {!data ? (
          <p>조회할 user_id를 입력하세요.</p>
        ) : (
          <>
            <section className="metric-grid">
              <div>
                <span>사용자</span>
                <strong>
                  #{data.user.user_id} {data.user.display_name}
                </strong>
              </div>
              <div>
                <span>전체 행</span>
                <strong>{formatNumber(data.ledger.summary.totalRows)}</strong>
              </div>
              <div>
                <span>open lot</span>
                <strong>{formatNumber(data.ledger.summary.openLotCount)}</strong>
              </div>
              <div>
                <span>최종 누적수익</span>
                <strong>{formatKrw(data.ledger.summary.finalCumulativeProfitKrw)}</strong>
              </div>
            </section>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>buyLot</th>
                    <th>매수일</th>
                    <th>매수금액</th>
                    <th>USD</th>
                    <th>매도일</th>
                    <th>매도금액</th>
                    <th>손익</th>
                    <th>상태</th>
                  </tr>
                </thead>
                <tbody>
                  {data.ledger.items.map((row) => (
                    <tr key={`${row.buyLotId}-${row.lotAllocationId ?? "open"}`}>
                      <td>{row.buyLotId}</td>
                      <td>{formatDate(row.buyDate)}</td>
                      <td>{formatKrw(row.buyKrwAmount)}</td>
                      <td>{formatUsd(row.usdAmount)}</td>
                      <td>{row.sellDate ? formatDate(row.sellDate) : ""}</td>
                      <td>{row.sellKrwAmount === null ? "" : formatKrw(row.sellKrwAmount)}</td>
                      <td>{formatKrw(row.profitKrw)}</td>
                      <td>{row.lotStatus}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function LedgerPage() {
  return (
    <AdminGuard>
      <LedgerContent />
    </AdminGuard>
  );
}

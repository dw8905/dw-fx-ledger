"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { AuthGuard } from "../../../../src/components/auth-guard";
import { formatDate, formatDateTime, formatDecimal, formatKrw } from "../../../../src/lib/format";
import {
  cancelSellTransaction,
  getSellTransaction,
  type SellTransaction
} from "../../../../src/lib/fx-api";

function SellTransactionDetailContent() {
  const params = useParams<{ sellTransactionId: string }>();
  const router = useRouter();
  const sellTransactionId = useMemo(
    () => Number(params.sellTransactionId),
    [params.sellTransactionId]
  );
  const [transaction, setTransaction] = useState<SellTransaction | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [error, setError] = useState("");
  const [isCancelling, setIsCancelling] = useState(false);

  useEffect(() => {
    getSellTransaction(sellTransactionId)
      .then(setTransaction)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매도 거래를 불러오지 못했습니다.")
      );
  }, [sellTransactionId]);

  async function handleCancel() {
    setError("");
    setIsCancelling(true);
    try {
      const updated = await cancelSellTransaction(
        sellTransactionId,
        cancelReason.trim() || "사용자 요청"
      );
      setTransaction(updated);
      setCancelReason("");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매도 취소에 실패했습니다.");
    } finally {
      setIsCancelling(false);
    }
  }

  return (
    <main className="content-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Ledger</p>
          <h1>매도 거래 상세</h1>
        </div>
        <button className="secondary-button" type="button" onClick={() => router.push("/fx/sell-transactions")}>
          목록
        </button>
      </section>

      {error ? <p className="form-error">{error}</p> : null}
      {!transaction ? (
        <p>매도 거래를 불러오는 중입니다.</p>
      ) : (
        <>
          <section className="detail-panel">
            <dl className="detail-grid">
              <div>
                <dt>번호</dt>
                <dd>{transaction.sellTransactionId}</dd>
              </div>
              <div>
                <dt>상태</dt>
                <dd>{transaction.transactionStatus}</dd>
              </div>
              <div>
                <dt>매도일</dt>
                <dd>{formatDate(transaction.sellDate)}</dd>
              </div>
              <div>
                <dt>매도 USD</dt>
                <dd>{formatDecimal(transaction.sellUsdAmount)} USD</dd>
              </div>
              <div>
                <dt>매도환율</dt>
                <dd>{formatDecimal(transaction.sellExchangeRate)}</dd>
              </div>
              <div>
                <dt>차감 전략</dt>
                <dd>{transaction.allocationStrategy}</dd>
              </div>
              <div>
                <dt>매수 원가</dt>
                <dd>{formatKrw(transaction.totalBuyKrwAmount)} KRW</dd>
              </div>
              <div>
                <dt>매도 원화</dt>
                <dd>{formatKrw(transaction.totalSellKrwAmount)} KRW</dd>
              </div>
              <div>
                <dt>실제손익</dt>
                <dd>{formatKrw(transaction.totalRealProfitKrw)} KRW</dd>
              </div>
              <div>
                <dt>표시손익</dt>
                <dd>{formatKrw(transaction.totalDisplayProfitKrw)} KRW</dd>
              </div>
              <div>
                <dt>등록일</dt>
                <dd>{formatDateTime(transaction.createdAt)}</dd>
              </div>
              <div>
                <dt>메모</dt>
                <dd>{transaction.memo || "-"}</dd>
              </div>
            </dl>
          </section>

          {transaction.transactionStatus === "completed" ? (
            <section className="detail-panel compact-panel">
              <h2>매도 취소</h2>
              <label>
                취소 사유
                <input
                  value={cancelReason}
                  onChange={(event) => setCancelReason(event.target.value)}
                />
              </label>
              <button className="danger-button" disabled={isCancelling} type="button" onClick={handleCancel}>
                {isCancelling ? "취소 중" : "매도 취소"}
              </button>
            </section>
          ) : null}

          <section className="detail-panel">
            <h2>로트 차감 내역</h2>
            <div className="table-wrap">
              <table className="post-table">
                <thead>
                  <tr>
                    <th>Allocation</th>
                    <th>Source</th>
                    <th>Sold</th>
                    <th>Remaining</th>
                    <th>USD</th>
                    <th>매수원가</th>
                    <th>매도원화</th>
                    <th>실제손익</th>
                  </tr>
                </thead>
                <tbody>
                  {(transaction.allocations || []).map((allocation) => (
                    <tr key={allocation.lotAllocationId}>
                      <td>{allocation.lotAllocationId}</td>
                      <td>
                        <Link href={`/fx/buy-lots/${allocation.sourceBuyLotId}/edit`}>
                          {allocation.sourceBuyLotId}
                        </Link>
                      </td>
                      <td>{allocation.closedBuyLotId}</td>
                      <td>{allocation.remainingBuyLotId || "-"}</td>
                      <td>{formatDecimal(allocation.allocatedUsdAmount)} USD</td>
                      <td>{formatKrw(allocation.allocatedBuyKrwAmount)} KRW</td>
                      <td>{formatKrw(allocation.allocatedSellKrwAmount)} KRW</td>
                      <td>{formatKrw(allocation.realProfitKrw)} KRW</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </main>
  );
}

export default function SellTransactionDetailPage() {
  return (
    <AuthGuard>
      <SellTransactionDetailContent />
    </AuthGuard>
  );
}

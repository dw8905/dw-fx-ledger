"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthGuard } from "../../../../src/components/auth-guard";
import { DateSegmentInput } from "../../../../src/components/date-segment-input";
import { createSellTransaction } from "../../../../src/lib/fx-api";

function NewSellTransactionContent() {
  const router = useRouter();
  const [sellDate, setSellDate] = useState("");
  const [sellUsdAmount, setSellUsdAmount] = useState("");
  const [sellExchangeRate, setSellExchangeRate] = useState("");
  const [allocationStrategy, setAllocationStrategy] = useState("highest_rate_first");
  const [memo, setMemo] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await createSellTransaction({
        sellDate,
        sellUsdAmount,
        sellExchangeRate,
        allocationStrategy,
        memo: memo.trim() || undefined
      });
      router.push("/fx/sell-transactions");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매도 등록에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="content-page narrow">
      <p className="eyebrow">FX Ledger</p>
      <h1>매도 등록</h1>
      <form className="post-form" onSubmit={handleSubmit}>
        <DateSegmentInput label="매도일" required value={sellDate} onChange={setSellDate} />
        <label>
          매도 USD 금액
          <input
            min="0.000001"
            required
            step="0.000001"
            type="number"
            value={sellUsdAmount}
            onChange={(event) => setSellUsdAmount(event.target.value)}
          />
        </label>
        <label>
          매도적용환율
          <input
            min="0.000001"
            required
            step="0.000001"
            type="number"
            value={sellExchangeRate}
            onChange={(event) => setSellExchangeRate(event.target.value)}
          />
        </label>
        <label>
          차감 전략
          <select
            value={allocationStrategy}
            onChange={(event) => setAllocationStrategy(event.target.value)}
          >
            <option value="highest_rate_first">highest_rate_first</option>
            <option value="fifo">fifo</option>
            <option value="lifo">lifo</option>
          </select>
        </label>
        <label>
          메모
          <textarea
            rows={4}
            value={memo}
            onChange={(event) => setMemo(event.target.value)}
          />
        </label>
        {error ? <p className="form-error">{error}</p> : null}
        <button className="primary-button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "저장 중" : "저장"}
        </button>
      </form>
    </main>
  );
}

export default function NewSellTransactionPage() {
  return (
    <AuthGuard>
      <NewSellTransactionContent />
    </AuthGuard>
  );
}

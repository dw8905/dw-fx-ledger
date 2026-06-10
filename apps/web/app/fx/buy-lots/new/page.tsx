"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthGuard } from "../../../../src/components/auth-guard";
import { DateSegmentInput } from "../../../../src/components/date-segment-input";
import { createBuyLot } from "../../../../src/lib/fx-api";

function NewBuyLotContent() {
  /** FX 매수 등록 폼 상태를 관리하고 저장 성공 시 목록으로 이동합니다. */

  const router = useRouter();
  const [buyDate, setBuyDate] = useState("");
  const [buyKrwAmount, setBuyKrwAmount] = useState("");
  const [buyExchangeRate, setBuyExchangeRate] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 입력된 매수일, 원화 금액, 환율로 새 매수 로트를 생성합니다. */

    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await createBuyLot({
        buyDate,
        buyKrwAmount: Number(buyKrwAmount),
        buyExchangeRate
      });
      router.push("/fx/buy-lots");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매수 로트 등록에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="content-page narrow">
      <p className="eyebrow">FX Ledger</p>
      <h1>매수 로트 등록</h1>
      <form className="post-form" onSubmit={handleSubmit}>
        <DateSegmentInput label="매수일" required value={buyDate} onChange={setBuyDate} />
        <label>
          매수원화환전금액
          <input
            min={1}
            required
            type="number"
            value={buyKrwAmount}
            onChange={(event) => setBuyKrwAmount(event.target.value)}
          />
        </label>
        <label>
          매수적용환율
          <input
            min="0.000001"
            required
            step="0.000001"
            type="number"
            value={buyExchangeRate}
            onChange={(event) => setBuyExchangeRate(event.target.value)}
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

export default function NewBuyLotPage() {
  /** FX 매수 등록 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <NewBuyLotContent />
    </AuthGuard>
  );
}

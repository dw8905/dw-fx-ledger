"use client";

import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AuthGuard } from "../../../../../src/components/auth-guard";
import { DateSegmentInput } from "../../../../../src/components/date-segment-input";
import { getBuyLot, getCurrencyOption, updateBuyLot, type BuyLot, type CurrencyCode } from "../../../../../src/lib/fx-api";

function EditBuyLotContent() {
  /** 수정 가능한 open 매수 로트를 불러와 편집 폼에 채웁니다. */

  const params = useParams<{ buyLotId: string }>();
  const router = useRouter();
  const buyLotId = Number(params.buyLotId);
  const [buyLot, setBuyLot] = useState<BuyLot | null>(null);
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>("USD");
  const [buyDate, setBuyDate] = useState("");
  const [buyKrwAmount, setBuyKrwAmount] = useState("");
  const [buyExchangeRate, setBuyExchangeRate] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    getBuyLot(buyLotId)
      .then((loaded) => {
        if (loaded.lotStatus !== "open" || !loaded.isActive) {
          setError("open 상태의 활성 매수 로트만 수정할 수 있습니다.");
          return;
        }

        setBuyLot(loaded);
        setCurrencyCode(loaded.currencyCode);
        setBuyDate(loaded.buyDate);
        setBuyKrwAmount(String(loaded.buyKrwAmount));
        setBuyExchangeRate(loaded.buyExchangeRate);
      })
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매수 로트를 불러오지 못했습니다.")
      );
  }, [buyLotId]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 편집된 매수 로트 입력값을 저장하고 목록으로 이동합니다. */

    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await updateBuyLot(buyLotId, {
        currencyCode,
        buyDate,
        buyKrwAmount: Number(buyKrwAmount),
        buyExchangeRate
      });
      router.push("/fx/buy-lots");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매수 로트 수정에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const selectedCurrency = getCurrencyOption(currencyCode);

  if (error && !buyLot) {
    return (
      <main className="content-page narrow">
        <p className="form-error">{error}</p>
      </main>
    );
  }

  if (!buyLot) {
    return <main className="content-page narrow">매수 로트를 불러오는 중입니다.</main>;
  }

  return (
    <main className="content-page narrow">
      <p className="eyebrow">FX Ledger</p>
      <h1>매수 로트 수정</h1>
      <form className="post-form" onSubmit={handleSubmit}>
        <label>
          통화
          <input disabled value={selectedCurrency.label} />
        </label>
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
          매수적용환율 ({selectedCurrency.amountLabel})
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
          {isSubmitting ? "수정 중" : "수정"}
        </button>
      </form>
    </main>
  );
}

export default function EditBuyLotPage() {
  /** FX 매수 로트 수정 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <EditBuyLotContent />
    </AuthGuard>
  );
}

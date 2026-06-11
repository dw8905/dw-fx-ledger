"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AuthGuard } from "../../../../src/components/auth-guard";
import { DateSegmentInput } from "../../../../src/components/date-segment-input";
import { formatDate, formatDecimal, formatForeignCurrency, formatKrw } from "../../../../src/lib/format";
import {
  createSellTransaction,
  currencyOptions,
  formatAllocationStrategy,
  getCurrencyOption,
  listOpenBuyLotsForSelection,
  type BuyLot,
  type CurrencyCode
} from "../../../../src/lib/fx-api";

function NewSellTransactionContent() {
  /** 매도 등록 폼과 수동 allocation 선택 상태를 함께 관리합니다. */

  const router = useRouter();
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>("USD");
  const [sellDate, setSellDate] = useState("");
  const [sellUsdAmount, setSellUsdAmount] = useState("");
  const [sellExchangeRate, setSellExchangeRate] = useState("");
  const [allocationStrategy, setAllocationStrategy] = useState("highest_rate_first");
  const [buyLots, setBuyLots] = useState<BuyLot[]>([]);
  const [manualAmounts, setManualAmounts] = useState<Record<number, string>>({});
  const [memo, setMemo] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const selectedTotalUsd = useMemo(
    () =>
      Object.values(manualAmounts).reduce(
        (total, value) => total + (Number(value) || 0),
        0
      ),
    [manualAmounts]
  );
  const sellUsdNumber = Number(sellUsdAmount) || 0;
  const manualDifference = sellUsdNumber - selectedTotalUsd;

  useEffect(() => {
    if (allocationStrategy !== "manual" || buyLots.length > 0) {
      return;
    }

    listOpenBuyLotsForSelection(currencyCode)
      .then((data) => setBuyLots(data.items))
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "매수 로트를 불러오지 못했습니다.")
      );
  }, [allocationStrategy, buyLots.length, currencyCode]);

  useEffect(() => {
    setBuyLots([]);
    setManualAmounts({});
  }, [currencyCode]);

  function toggleManualLot(lot: BuyLot, checked: boolean) {
    /** 수동 차감 로트를 선택/해제하고 선택 시 남은 필요 외화만큼 기본값을 채웁니다. */

    setManualAmounts((current) => {
      const next = { ...current };
      if (!checked) {
        delete next[lot.buyLotId];
        return next;
      }

      const currentTotalWithoutLot = Object.entries(current).reduce(
        (total, [buyLotId, value]) =>
          Number(buyLotId) === lot.buyLotId ? total : total + (Number(value) || 0),
        0
      );
      const remainingNeed = Math.max((Number(sellUsdAmount) || 0) - currentTotalWithoutLot, 0);
      next[lot.buyLotId] = String(Math.min(Number(lot.usdAmount), remainingNeed || Number(lot.usdAmount)));
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 수동 차감 합계 검증 후 매도 거래 생성 API를 호출합니다. */

    event.preventDefault();
    setError("");

    if (allocationStrategy === "manual" && Math.abs(manualDifference) > 0.000001) {
      setError(`직접 선택한 ${selectedCurrency.amountLabel} 합계가 매도 ${selectedCurrency.amountLabel} 금액과 같아야 합니다.`);
      return;
    }

    setIsSubmitting(true);

    try {
      await createSellTransaction({
        currencyCode,
        sellDate,
        sellUsdAmount,
        sellExchangeRate,
        allocationStrategy,
        manualAllocations:
          allocationStrategy === "manual"
            ? Object.entries(manualAmounts).map(([buyLotId, usdAmount]) => ({
                buyLotId: Number(buyLotId),
                usdAmount
              }))
            : undefined,
        memo: memo.trim() || undefined
      });
      router.push("/fx/sell-transactions");
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "매도 등록에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const selectedCurrency = getCurrencyOption(currencyCode);

  return (
    <main className="content-page narrow">
      <p className="eyebrow">FX Ledger</p>
      <h1>매도 등록</h1>
      <form className="post-form" onSubmit={handleSubmit}>
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
        <DateSegmentInput label="매도일" required value={sellDate} onChange={setSellDate} />
        <label>
          매도 {selectedCurrency.amountLabel} 금액
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
            <option value="highest_rate_first">{formatAllocationStrategy("highest_rate_first")}</option>
            <option value="fifo">{formatAllocationStrategy("fifo")}</option>
            <option value="lifo">{formatAllocationStrategy("lifo")}</option>
            <option value="manual">{formatAllocationStrategy("manual")}</option>
          </select>
        </label>
        {allocationStrategy === "manual" ? (
          <section className="manual-allocation-panel">
            <div className="manual-allocation-summary">
              <strong>선택 합계 {formatForeignCurrency(String(selectedTotalUsd || 0), currencyCode)}</strong>
              <span>
                차이 {formatForeignCurrency(String(manualDifference || 0), currencyCode)}
              </span>
            </div>
            <div className="table-wrap">
              <table className="post-table compact-table">
                <thead>
                  <tr>
                    <th>선택</th>
                    <th>매수일</th>
                    <th>잔여 {selectedCurrency.amountLabel}</th>
                    <th>매수환율</th>
                    <th>원화</th>
                    <th>차감 {selectedCurrency.amountLabel}</th>
                  </tr>
                </thead>
                <tbody>
                  {buyLots.length === 0 ? (
                    <tr>
                      <td colSpan={6}>선택 가능한 open 매수 로트가 없습니다.</td>
                    </tr>
                  ) : (
                    buyLots.map((lot) => (
                      <tr key={lot.buyLotId}>
                        <td>
                          <input
                            aria-label={`${lot.buyLotId} 선택`}
                            checked={manualAmounts[lot.buyLotId] !== undefined}
                            type="checkbox"
                            onChange={(event) => toggleManualLot(lot, event.target.checked)}
                          />
                        </td>
                        <td>{formatDate(lot.buyDate)}</td>
                        <td>{formatForeignCurrency(lot.usdAmount, lot.currencyCode)}</td>
                        <td>{formatDecimal(lot.buyExchangeRate)}</td>
                        <td>{formatKrw(lot.buyKrwAmount)} KRW</td>
                        <td>
                          <input
                            min="0.000001"
                            step="0.000001"
                            type="number"
                            value={manualAmounts[lot.buyLotId] || ""}
                            onChange={(event) =>
                              setManualAmounts((current) => ({
                                ...current,
                                [lot.buyLotId]: event.target.value
                              }))
                            }
                          />
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
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
  /** FX 매도 등록 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <NewSellTransactionContent />
    </AuthGuard>
  );
}

"use client";

import { FormEvent, Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AuthGuard } from "../../src/components/auth-guard";
import { Pagination } from "../../src/components/pagination";
import { SectionTabs, type SectionTabItem } from "../../src/components/section-tabs";
import { formatDate, formatKrwCurrency } from "../../src/lib/format";
import {
  cancelItemTrade,
  createItemTrade,
  listItemCodes,
  listItemTrades,
  type ItemCode,
  type ItemCodeSummary,
  type ItemTrade,
  type ItemTradeListResponse
} from "../../src/lib/item-trades-api";

/** 자산관리 화면에서 URL 쿼리로 선택되는 상위 탭입니다. */
type ItemTab = "buy" | "sell" | "inventory";
/** 서버 거래 타입과 맞춰 쓰는 매수/매도/재고조정 구분값입니다. */
type TradeType = "buy" | "sell" | "adjustment";

const tabs: Array<SectionTabItem<ItemTab>> = [
  { id: "buy", href: "/item-trades?tab=buy", label: "매수" },
  { id: "sell", href: "/item-trades?tab=sell", label: "매도" },
  { id: "inventory", href: "/item-trades?tab=inventory", label: "자산별 재고관리" }
];

function parseItemTab(value: string | null): ItemTab {
  /** URL tab 쿼리값을 허용된 자산관리 탭 값으로 정규화합니다. */

  if (value === "sell" || value === "inventory") {
    return value;
  }
  return "buy";
}

function today() {
  /** 한국 날짜 기준으로 input[type=date]에 넣을 오늘 YYYY-MM-DD 값을 만듭니다. */

  const parts = new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    month: "2-digit",
    timeZone: "Asia/Seoul",
    year: "numeric"
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

function toNumber(value: string) {
  /** 숫자 입력 문자열을 안전하게 number로 바꾸고 비정상 값은 0으로 처리합니다. */

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function calculateMinimumProfitableUnitPrice(unitPrice: number, feePercent: number) {
  /** 판매 수수료율을 감안해 평균단가 이상이 남는 최소 판매가를 계산합니다. */

  const netRate = 1 - feePercent / 100;
  if (unitPrice <= 0 || netRate <= 0) {
    return 0;
  }
  return Math.ceil(unitPrice / netRate);
}

function formatFeeRate(value: string) {
  /** 서버가 0.05 형태로 내려준 수수료율을 5%처럼 표시합니다. */

  return `${(Number(value) * 100).toLocaleString("ko-KR", {
    maximumFractionDigits: 2
  })}%`;
}

function findCodeByName(codes: ItemCode[], itemName: string) {
  /** 사용자가 입력한 자산명과 동일한 활성 자산 마스터를 찾습니다. */

  return codes.find((code) => code.itemName === itemName.trim()) ?? null;
}

function ItemTradeForm({
  codes,
  onSaved,
  summaries,
  tradeType
}: {
  codes: ItemCode[];
  onSaved: () => Promise<void>;
  summaries: ItemCodeSummary[];
  tradeType: TradeType;
}) {
  /** 매수/매도/조정 타입별 공통 입력 폼과 예상 손익 프리뷰를 렌더링합니다. */

  const [itemName, setItemName] = useState("");
  const [tradeDate, setTradeDate] = useState(today);
  const [unitPrice, setUnitPrice] = useState("0");
  const [quantity, setQuantity] = useState("1");
  const [feePercent, setFeePercent] = useState("5");
  const [memo, setMemo] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const selectedCode = findCodeByName(codes, itemName);
  const selectedSummary = selectedCode
    ? summaries.find((summary) => summary.itemCode === selectedCode.itemCode) ?? null
    : null;
  const unitPriceNumber = toNumber(unitPrice);
  const quantityNumber = toNumber(quantity);
  const feePercentNumber = toNumber(feePercent);
  const totalAmount = unitPriceNumber * quantityNumber;
  const feeAmount =
    tradeType === "sell" && totalAmount > 0 ? Math.ceil(totalAmount * (feePercentNumber / 100)) : null;
  const netSellAmount = feeAmount !== null ? totalAmount - feeAmount : null;
  const costBasis =
    tradeType === "sell" && selectedSummary
      ? selectedSummary.averageBuyUnitPrice * quantityNumber
      : null;
  const profitAmount =
    netSellAmount !== null && costBasis !== null ? netSellAmount - costBasis : null;
  const buyPreviewQuantity = tradeType === "buy" ? (selectedSummary?.inventoryQuantity ?? 0) + quantityNumber : 0;
  const buyPreviewValue = tradeType === "buy" ? (selectedSummary?.inventoryValue ?? 0) + totalAmount : 0;
  const buyPreviewAverageUnitPrice =
    tradeType === "buy" && buyPreviewQuantity > 0 ? Math.ceil(buyPreviewValue / buyPreviewQuantity) : 0;
  const maxSellQuantity = selectedSummary?.inventoryQuantity ?? 0;
  const previewMinimumProfitableUnitPrice =
    tradeType === "buy"
      ? calculateMinimumProfitableUnitPrice(buyPreviewAverageUnitPrice, feePercentNumber)
      : calculateMinimumProfitableUnitPrice(selectedSummary?.averageBuyUnitPrice ?? 0, feePercentNumber);

  function handleUseMaxQuantity() {
    /** 매도 탭에서 현재 보유 수량을 수량 입력값으로 한 번에 채웁니다. */

    if (maxSellQuantity > 0) {
      setQuantity(String(maxSellQuantity));
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 자산 마스터 선택 여부를 확인한 뒤 거래 등록 API를 호출합니다. */

    event.preventDefault();
    setError("");
    if (!selectedCode) {
      setError("관리자에 등록된 자산명을 선택해주세요.");
      return;
    }

    setSaving(true);
    try {
      await createItemTrade({
        itemCode: selectedCode.itemCode,
        itemName: selectedCode.itemName,
        tradeType,
        tradeDate,
        unitPrice: unitPriceNumber,
        quantity: quantityNumber,
        feeRate: String(feePercentNumber / 100),
        memo: memo || undefined
      });
      setTradeDate(today());
      setUnitPrice("0");
      setQuantity("1");
      setFeePercent("5");
      setMemo("");
      await onSaved();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "거래 기록 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="post-form trade-form" onSubmit={(event) => void handleSubmit(event)}>
      <div className="form-grid">
        <label>
          자산명
          <input
            required
            list="item-name-options"
            value={itemName}
            onChange={(event) => setItemName(event.target.value)}
          />
        </label>
        <label>
          거래일
          <input
            required
            type="date"
            value={tradeDate}
            onChange={(event) => setTradeDate(event.target.value)}
          />
        </label>
        <label>
          {tradeType === "buy" ? "매수 단가" : "매도 단가"}
          <input
            required
            min={1}
            type="number"
            value={unitPrice}
            onChange={(event) => setUnitPrice(event.target.value)}
          />
        </label>
        <label>
          <span className="field-label-row">
            수량
            {tradeType === "sell" ? (
              <button
                className="field-action-button"
                disabled={maxSellQuantity <= 0}
                type="button"
                onClick={handleUseMaxQuantity}
              >
                최대
              </button>
            ) : null}
          </span>
          <input
            required
            min={1}
            max={tradeType === "sell" && maxSellQuantity > 0 ? maxSellQuantity : undefined}
            type="number"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
          />
        </label>
        <label>
          판매 수수료 %
          <input
            required
            min={0}
            max={99}
            step="0.01"
            type="number"
            value={feePercent}
            onChange={(event) => setFeePercent(event.target.value)}
          />
        </label>
      </div>
      <datalist id="item-name-options">
        {codes.map((code) => (
          <option key={code.itemCodeId} value={code.itemName} />
        ))}
      </datalist>
      <label>
        메모
        <textarea value={memo} onChange={(event) => setMemo(event.target.value)} />
      </label>
      <div className="trade-inline-summary">
        <span>현재 보유 {selectedSummary?.inventoryQuantity ?? 0}</span>
        <span>
          평균단가{" "}
          {formatKrwCurrency(tradeType === "buy" ? buyPreviewAverageUnitPrice : selectedSummary?.averageBuyUnitPrice ?? 0)}
        </span>
        <span>최소판매가 {formatKrwCurrency(previewMinimumProfitableUnitPrice)}</span>
        {tradeType === "sell" ? (
          <>
            <span>예상 수수료 {feeAmount === null ? "-" : formatKrwCurrency(feeAmount)}</span>
            <span>예상 손익 {profitAmount === null ? "-" : formatKrwCurrency(profitAmount)}</span>
          </>
        ) : (
          <span>총 매수금액 {formatKrwCurrency(totalAmount)}</span>
        )}
      </div>
      {error ? <p className="form-error">{error}</p> : null}
      <button className="primary-button" disabled={saving} type="submit">
        {saving ? "저장 중" : `${tradeType === "buy" ? "매수" : "매도"} 등록`}
      </button>
    </form>
  );
}

function TradeTable({
  items,
  onCancelled,
  tradeType
}: {
  items: ItemTrade[];
  onCancelled: () => Promise<void>;
  tradeType: TradeType;
}) {
  /** 매수/매도/조정 거래 목록을 공통 테이블로 보여주고 취소 액션을 제공합니다. */

  async function handleCancel(trade: ItemTrade) {
    /** 취소 사유를 입력받아 해당 거래를 취소하고 목록을 새로고침합니다. */

    const tradeLabel = tradeType === "buy" ? "매수" : tradeType === "sell" ? "매도" : "조정";
    const reason = window.prompt(`${trade.itemName} ${tradeLabel} 기록을 취소할까요? 취소 사유를 입력할 수 있습니다.`);
    if (reason === null) {
      return;
    }

    await cancelItemTrade(trade.itemTradeId, reason);
    await onCancelled();
  }

  return (
    <div className="table-wrap">
      <table className="post-table">
        <thead>
          <tr>
            <th>자산명</th>
            <th>상태</th>
            <th>거래일</th>
            <th>{tradeType === "adjustment" ? "조정단가" : "단가"}</th>
            <th>{tradeType === "adjustment" ? "조정수량" : "수량"}</th>
            <th>평균단가</th>
            <th>최소판매가</th>
            {tradeType === "sell" ? (
              <>
                <th>수수료율</th>
                <th>수수료</th>
                <th>손익</th>
              </>
            ) : null}
            <th>잔여수량</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={tradeType === "sell" ? 12 : 9}>기록이 없습니다.</td>
            </tr>
          ) : (
            items.map((trade) => (
              <tr key={trade.itemTradeId}>
                <td>{trade.itemName}</td>
                <td>{trade.tradeStatus === "active" ? "정상" : "취소"}</td>
                <td>{formatDate(trade.tradeDate)}</td>
                <td>{formatKrwCurrency(trade.unitPrice)}</td>
                <td>{trade.quantity}</td>
                <td>{formatKrwCurrency(trade.averageBuyUnitPrice ?? 0)}</td>
                <td>{formatKrwCurrency(trade.minimumProfitableUnitPrice)}</td>
                {tradeType === "sell" ? (
                  <>
                    <td>{formatFeeRate(trade.feeRate)}</td>
                    <td>{trade.feeAmount === null ? "-" : formatKrwCurrency(trade.feeAmount)}</td>
                    <td className={trade.profitAmount !== null && trade.profitAmount > 0 ? "profit-strong" : ""}>
                      {trade.profitAmount === null ? "-" : formatKrwCurrency(trade.profitAmount)}
                    </td>
                  </>
                ) : null}
                <td>{trade.inventoryQuantityAfter ?? "-"}</td>
                <td>
                  {trade.tradeStatus === "active" ? (
                    <button className="link-button danger-link" type="button" onClick={() => void handleCancel(trade)}>
                      취소
                    </button>
                  ) : (
                    "-"
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function InventoryTable({
  onAdjusted,
  summaries
}: {
  onAdjusted: (summary: ItemCodeSummary) => void;
  summaries: ItemCodeSummary[];
}) {
  /** 자산별 현재 재고, 평균단가, 최소판매가, 총 수익과 조정 버튼을 보여줍니다. */

  return (
    <div className="table-wrap">
      <table className="post-table">
        <thead>
          <tr>
            <th>자산명</th>
            <th>남은 수량</th>
            <th>재고 원가</th>
            <th>평균단가</th>
            <th>최소 이득 판매가</th>
            <th>총 수익</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          {summaries.length === 0 ? (
            <tr>
              <td colSpan={7}>재고가 없습니다.</td>
            </tr>
          ) : (
            summaries.map((summary) => (
              <tr key={summary.itemCodeId}>
                <td>{summary.itemName}</td>
                <td>{summary.inventoryQuantity}</td>
                <td>{formatKrwCurrency(summary.inventoryValue)}</td>
                <td>{formatKrwCurrency(summary.averageBuyUnitPrice)}</td>
                <td>{formatKrwCurrency(summary.minimumProfitableUnitPrice)}</td>
                <td className={summary.totalProfitAmount > 0 ? "profit-strong" : ""}>
                  {formatKrwCurrency(summary.totalProfitAmount)}
                </td>
                <td>
                  <button className="link-button" type="button" onClick={() => onAdjusted(summary)}>
                    조정
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function ItemTradesContent() {
  /** 자산관리 탭 상태, 거래 목록, 자산 마스터 목록, 재고 조정 흐름을 관리합니다. */

  const searchParams = useSearchParams();
  const activeTab = parseItemTab(searchParams.get("tab"));
  const [codes, setCodes] = useState<ItemCode[]>([]);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<ItemTradeListResponse | null>(null);
  const [error, setError] = useState("");

  const loadCodes = useCallback(() => {
    /** 관리자에서 등록한 활성 자산 마스터를 자동완성 목록으로 불러옵니다. */

    listItemCodes()
      .then((response) => setCodes(response.items))
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "자산 목록을 불러오지 못했습니다.")
      );
  }, []);

  const loadTrades = useCallback(() => {
    /** 현재 페이지/크기에 맞춰 사용자 자산 거래와 재고 요약을 불러옵니다. */

    listItemTrades(page, size)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "거래 기록을 불러오지 못했습니다.")
      );
  }, [page, size]);

  useEffect(() => {
    loadCodes();
  }, [loadCodes]);

  useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  useEffect(() => {
    setPage(1);
  }, [activeTab]);

  const buyItems = useMemo(
    () => data?.items.filter((item) => item.tradeType === "buy") ?? [],
    [data]
  );
  const sellItems = useMemo(
    () => data?.items.filter((item) => item.tradeType === "sell") ?? [],
    [data]
  );
  const adjustmentItems = useMemo(
    () => data?.items.filter((item) => item.tradeType === "adjustment") ?? [],
    [data]
  );

  async function refreshAfterSave() {
    /** 거래 저장/취소 후 첫 페이지 기준으로 코드 목록과 거래 목록을 다시 동기화합니다. */

    setPage(1);
    await Promise.all([loadCodes(), listItemTrades(1, size).then(setData)]);
  }

  async function handleInventoryAdjust(summary: ItemCodeSummary) {
    /** 실제 보유 수량을 입력받아 차이만큼 adjustment 거래를 새로 기록합니다. */

    const actualQuantityText = window.prompt(
      `${summary.itemName} 실제 보유 수량을 입력해주세요.`,
      String(summary.inventoryQuantity)
    );
    if (actualQuantityText === null) {
      return;
    }

    const actualQuantity = Number(actualQuantityText);
    if (!Number.isInteger(actualQuantity) || actualQuantity < 0) {
      setError("실제 보유 수량은 0 이상의 정수로 입력해주세요.");
      return;
    }

    const quantityDelta = actualQuantity - summary.inventoryQuantity;
    if (quantityDelta === 0) {
      return;
    }

    let unitPrice = summary.averageBuyUnitPrice || 1;
    if (quantityDelta > 0) {
      const unitPriceText = window.prompt(
        `${summary.itemName} 증가 수량에 적용할 단가를 입력해주세요.`,
        String(unitPrice)
      );
      if (unitPriceText === null) {
        return;
      }

      unitPrice = Number(unitPriceText);
      if (!Number.isInteger(unitPrice) || unitPrice <= 0) {
        setError("조정 단가는 1 이상의 정수로 입력해주세요.");
        return;
      }
    }

    const reason = window.prompt("조정 사유를 입력해주세요.", "실제 재고 수량 보정");
    if (reason === null) {
      return;
    }

    try {
      await createItemTrade({
        itemCode: summary.itemCode,
        itemName: summary.itemName,
        tradeType: "adjustment",
        tradeDate: today(),
        unitPrice,
        quantity: quantityDelta,
        feeRate: "0.05",
        memo: reason || "실제 재고 수량 보정"
      });
      await refreshAfterSave();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "재고 조정에 실패했습니다.");
    }
  }

  return (
    <>
      <div className="section-tabs-frame">
        <SectionTabs activeId={activeTab} ariaLabel="자산관리 기능" items={tabs} />
      </div>

      <main className="content-page trade-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Asset Management</p>
            <h1>자산관리</h1>
          </div>
        </section>

        {error ? <p className="form-error">{error}</p> : null}
        {activeTab === "buy" ? (
          <>
            <ItemTradeForm
              codes={codes}
              summaries={data?.summaries ?? []}
              tradeType="buy"
              onSaved={refreshAfterSave}
            />
            <h2 className="section-title">매수 트랜잭션</h2>
            <TradeTable items={buyItems} tradeType="buy" onCancelled={refreshAfterSave} />
          </>
        ) : null}
        {activeTab === "sell" ? (
          <>
            <ItemTradeForm
              codes={codes}
              summaries={data?.summaries ?? []}
              tradeType="sell"
              onSaved={refreshAfterSave}
            />
            <h2 className="section-title">매도 트랜잭션</h2>
            <TradeTable items={sellItems} tradeType="sell" onCancelled={refreshAfterSave} />
          </>
        ) : null}
        {activeTab === "inventory" ? (
          <>
            <h2 className="section-title">자산별 재고관리</h2>
            <InventoryTable summaries={data?.summaries ?? []} onAdjusted={(summary) => void handleInventoryAdjust(summary)} />
            <h2 className="section-title">재고 조정 기록</h2>
            <TradeTable items={adjustmentItems} tradeType="adjustment" onCancelled={refreshAfterSave} />
          </>
        ) : null}

        {activeTab !== "inventory" && data ? (
          <Pagination
            page={data.page}
            size={data.size}
            totalCount={data.totalCount}
            onPageChange={setPage}
            onSizeChange={(nextSize) => {
              setSize(nextSize);
              setPage(1);
            }}
          />
        ) : null}
      </main>
    </>
  );
}

export default function ItemTradesPage() {
  /** 자산관리 화면 전체를 인증 가드와 Suspense 경계로 감쌉니다. */

  return (
    <AuthGuard>
      <Suspense fallback={<main className="content-page trade-page">자산관리 화면을 불러오는 중입니다.</main>}>
        <ItemTradesContent />
      </Suspense>
    </AuthGuard>
  );
}

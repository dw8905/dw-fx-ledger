"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { AuthGuard } from "../../src/components/auth-guard";
import { Pagination } from "../../src/components/pagination";
import { formatDate, formatDateTime, formatKrwCurrency } from "../../src/lib/format";
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

type ItemTab = "buy" | "sell" | "inventory";
type TradeType = "buy" | "sell";

const tabs: Array<{ id: ItemTab; label: string }> = [
  { id: "buy", label: "매수" },
  { id: "sell", label: "매도" },
  { id: "inventory", label: "아이템별 재고관리" }
];

function today() {
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
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatFeeRate(value: string) {
  return `${(Number(value) * 100).toLocaleString("ko-KR", {
    maximumFractionDigits: 2
  })}%`;
}

function findCodeByName(codes: ItemCode[], itemName: string) {
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
  const [itemName, setItemName] = useState("");
  const [tradeDate, setTradeDate] = useState(today);
  const [unitPrice, setUnitPrice] = useState("1300000");
  const [quantity, setQuantity] = useState("1");
  const [feePercent, setFeePercent] = useState(tradeType === "sell" ? "5" : "0");
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
  const effectiveFeePercent = tradeType === "buy" ? 0 : feePercentNumber;
  const totalAmount = unitPriceNumber * quantityNumber;
  const feeAmount =
    tradeType === "sell" && totalAmount > 0 ? Math.ceil(totalAmount * (effectiveFeePercent / 100)) : null;
  const netSellAmount = feeAmount !== null ? totalAmount - feeAmount : null;
  const costBasis =
    tradeType === "sell" && selectedSummary
      ? selectedSummary.averageBuyUnitPrice * quantityNumber
      : null;
  const profitAmount =
    netSellAmount !== null && costBasis !== null ? netSellAmount - costBasis : null;

  useEffect(() => {
    setFeePercent(tradeType === "sell" ? "5" : "0");
  }, [tradeType]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!selectedCode) {
      setError("관리자에 등록된 아이템명을 선택해주세요.");
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
        feeRate: String(effectiveFeePercent / 100),
        memo: memo || undefined
      });
      setTradeDate(today());
      setUnitPrice("1300000");
      setQuantity("1");
      setFeePercent(tradeType === "sell" ? "5" : "0");
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
          아이템명
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
          수량
          <input
            required
            min={1}
            type="number"
            value={quantity}
            onChange={(event) => setQuantity(event.target.value)}
          />
        </label>
        {tradeType === "sell" ? (
          <label>
            수수료 %
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
        ) : null}
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
        <span>평균단가 {formatKrwCurrency(selectedSummary?.averageBuyUnitPrice ?? 0)}</span>
        <span>최소판매가 {formatKrwCurrency(selectedSummary?.minimumProfitableUnitPrice ?? 0)}</span>
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
  async function handleCancel(trade: ItemTrade) {
    const reason = window.prompt(`${trade.itemName} ${tradeType === "buy" ? "매수" : "매도"} 기록을 취소할까요? 취소 사유를 입력할 수 있습니다.`);
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
            <th>아이템명</th>
            <th>상태</th>
            <th>거래일</th>
            <th>단가</th>
            <th>수량</th>
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
            <th>등록일</th>
            <th>작업</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 ? (
            <tr>
              <td colSpan={tradeType === "sell" ? 13 : 10}>기록이 없습니다.</td>
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
                <td>{formatDateTime(trade.createdAt)}</td>
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

function InventoryTable({ summaries }: { summaries: ItemCodeSummary[] }) {
  return (
    <div className="table-wrap">
      <table className="post-table">
        <thead>
          <tr>
            <th>아이템명</th>
            <th>남은 수량</th>
            <th>재고 원가</th>
            <th>평균단가</th>
            <th>최소 이득 판매가</th>
            <th>총 수익</th>
          </tr>
        </thead>
        <tbody>
          {summaries.length === 0 ? (
            <tr>
              <td colSpan={6}>재고가 없습니다.</td>
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
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function ItemTradesContent() {
  const [activeTab, setActiveTab] = useState<ItemTab>("buy");
  const [codes, setCodes] = useState<ItemCode[]>([]);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<ItemTradeListResponse | null>(null);
  const [error, setError] = useState("");

  const loadCodes = useCallback(() => {
    listItemCodes()
      .then((response) => setCodes(response.items))
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "아이템 목록을 불러오지 못했습니다.")
      );
  }, []);

  const loadTrades = useCallback(() => {
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

  const buyItems = useMemo(
    () => data?.items.filter((item) => item.tradeType === "buy") ?? [],
    [data]
  );
  const sellItems = useMemo(
    () => data?.items.filter((item) => item.tradeType === "sell") ?? [],
    [data]
  );

  async function refreshAfterSave() {
    setPage(1);
    await Promise.all([loadCodes(), listItemTrades(1, size).then(setData)]);
  }

  return (
    <main className="content-page trade-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">Item Trade</p>
          <h1>아이템</h1>
        </div>
      </section>

      <nav className="sub-tabs" aria-label="아이템 기능">
        {tabs.map((tab) => (
          <button
            aria-current={activeTab === tab.id ? "page" : undefined}
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </nav>

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
          <h2 className="section-title">아이템별 재고관리</h2>
          <InventoryTable summaries={data?.summaries ?? []} />
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
  );
}

export default function ItemTradesPage() {
  return (
    <AuthGuard>
      <ItemTradesContent />
    </AuthGuard>
  );
}

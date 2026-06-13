"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { AuthGuard } from "../../../src/components/auth-guard";
import {
  formatCompactDate,
  formatForeignCurrency,
  formatKrw,
  formatKrwCurrency,
  formatKrwRate
} from "../../../src/lib/format";
import {
  currencyOptions,
  getCurrencyOption,
  getLedger,
  type CurrencyCode,
  type LedgerResponse,
  type LedgerRow
} from "../../../src/lib/fx-api";

const periodOptions = [
  { value: "all", label: "전체" },
  { value: "1y", label: "최근 1년" },
  { value: "3y", label: "최근 3년" },
  { value: "5y", label: "최근 5년" },
  { value: "latest", label: "마지막 날짜만" }
];

type MultiLinePoint = {
  /** 전체/USD/JPY 누적수익 선을 한 차트에 겹쳐 그리기 위한 점입니다. */
  label: string;
  total: number;
  USD: number | null;
  JPY: number | null;
};

type BarPoint = {
  /** 막대 차트에서 구간/월 라벨과 집계값을 표현하는 점입니다. */
  label: string;
  value: number;
};

type StatsCurrencyCode = CurrencyCode | "ALL";
type ProfitLineKey = "total" | CurrencyCode;

const statsCurrencyOptions: Array<{ code: StatsCurrencyCode; label: string }> = [
  { code: "ALL", label: "전체" },
  ...currencyOptions.map((option) => ({ code: option.code, label: option.label }))
];

const profitLineOptions: Array<{ key: ProfitLineKey; label: string; className: string }> = [
  { key: "total", label: "전체", className: "legend-total" },
  { key: "USD", label: "USD", className: "legend-usd" },
  { key: "JPY", label: "JPY", className: "legend-jpy" }
];

function CurrencyTooltip({ active, label, payload }: {
  active?: boolean;
  label?: string;
  payload?: Array<{ value?: number }>;
}) {
  /** 금액 차트 hover 시 원화 포맷으로 값을 보여주는 Recharts 커스텀 툴팁입니다. */

  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      <strong>{formatKrwCurrency(Number(payload[0].value ?? 0))}</strong>
    </div>
  );
}

function CountTooltip({ active, label, payload }: {
  active?: boolean;
  label?: string;
  payload?: Array<{ value?: number }>;
}) {
  /** 건수 차트 hover 시 정수 건수를 보여주는 Recharts 커스텀 툴팁입니다. */

  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      <strong>{formatKrw(Number(payload[0].value ?? 0))}건</strong>
    </div>
  );
}

function MultiCurrencyTooltip({ active, label, payload }: {
  active?: boolean;
  label?: string;
  payload?: Array<{ color?: string; dataKey?: string; name?: string; value?: number | null }>;
}) {
  /** 누적수익 차트 hover 시 전체/USD/JPY 값을 함께 보여줍니다. */

  const visiblePayload = payload?.filter((item) => item.value !== null && item.value !== undefined) ?? [];
  if (!active || visiblePayload.length === 0) {
    return null;
  }

  return (
    <div className="chart-tooltip">
      <span>{label}</span>
      {visiblePayload.map((item) => (
        <strong key={item.dataKey} style={{ color: item.color }}>
          {item.name}: {formatKrwCurrency(Number(item.value ?? 0))}
        </strong>
      ))}
    </div>
  );
}

function CumulativeProfitChart({ points }: { points: MultiLinePoint[] }) {
  /** 매도 allocation 순서에 따른 전체/USD/JPY 누적수익 흐름을 선형 차트로 표시합니다. */

  const [visibleLines, setVisibleLines] = useState<Record<ProfitLineKey, boolean>>({
    total: true,
    USD: true,
    JPY: true
  });
  const lastPoint = points.at(-1);

  function toggleLine(lineKey: ProfitLineKey) {
    /** 범례 버튼 클릭 시 해당 누적수익 선을 차트에서 보이거나 숨깁니다. */

    setVisibleLines((current) => ({ ...current, [lineKey]: !current[lineKey] }));
  }

  return (
    <div className="chart-card wide">
      <div className="chart-heading">
        <div>
          <h2>누적수익 추이</h2>
          <span>전체 KRW 손익과 통화별 누적 흐름</span>
          <div className="chart-legend">
            {profitLineOptions.map((option) => (
              <button
                aria-pressed={visibleLines[option.key]}
                className="chart-legend-button"
                key={option.key}
                type="button"
                onClick={() => toggleLine(option.key)}
              >
                <i className={option.className} />
                {option.label}
              </button>
            ))}
          </div>
        </div>
        <strong>{lastPoint ? formatKrwCurrency(lastPoint.total) : "-"}</strong>
      </div>
      {points.length === 0 ? (
        <p className="empty-chart">매도 기록이 없습니다.</p>
      ) : (
        <div className="chart-canvas resizable">
          <ResponsiveContainer height="100%" width="100%">
            <LineChart data={points} margin={{ bottom: 8, left: 8, right: 20, top: 12 }}>
              <CartesianGrid stroke="#dce4dd" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="label" minTickGap={24} tick={{ fill: "#52705e", fontSize: 12 }} tickLine={false} />
              <YAxis
                tick={{ fill: "#52705e", fontSize: 12 }}
                tickFormatter={(value) => formatKrw(Number(value))}
                tickLine={false}
                width={82}
              />
              <Tooltip content={<MultiCurrencyTooltip />} />
              {visibleLines.total ? (
                <Line
                  activeDot={{ r: 5 }}
                  dataKey="total"
                  dot={{ r: 3 }}
                  isAnimationActive={false}
                  name="전체"
                  stroke="#20352a"
                  strokeWidth={3}
                  type="monotone"
                />
              ) : null}
              {visibleLines.USD ? (
                <Line
                  activeDot={{ r: 4 }}
                  connectNulls
                  dataKey="USD"
                  dot={{ r: 2 }}
                  isAnimationActive={false}
                  name="USD"
                  stroke="#2e6140"
                  strokeWidth={2}
                  type="monotone"
                />
              ) : null}
              {visibleLines.JPY ? (
                <Line
                  activeDot={{ r: 4 }}
                  connectNulls
                  dataKey="JPY"
                  dot={{ r: 2 }}
                  isAnimationActive={false}
                  name="JPY"
                  stroke="#8b5e00"
                  strokeWidth={2}
                  type="monotone"
                />
              ) : null}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function StatsBarChart({
  emptyText,
  formatter,
  points,
  title,
  subtitle
}: {
  emptyText: string;
  formatter: (value: number) => string;
  points: BarPoint[];
  title: string;
  subtitle: string;
}) {
  /** 월별 손익이나 환율 구간 건수처럼 막대 형태의 통계를 공통 렌더링합니다. */

  return (
    <div className="chart-card">
      <div className="chart-heading">
        <div>
          <h2>{title}</h2>
          <span>{subtitle}</span>
        </div>
      </div>
      {points.length === 0 ? (
        <p className="empty-chart">{emptyText}</p>
      ) : (
        <div className="chart-canvas compact">
          <ResponsiveContainer height={260} width="100%">
            <BarChart data={points} margin={{ bottom: 8, left: 0, right: 12, top: 12 }}>
              <CartesianGrid stroke="#edf2ee" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="label" minTickGap={12} tick={{ fill: "#52705e", fontSize: 12 }} tickLine={false} />
              <YAxis
                tick={{ fill: "#52705e", fontSize: 12 }}
                tickFormatter={(value) => formatter(Number(value)).replace("₩", "")}
                tickLine={false}
                width={76}
              />
              <Tooltip content={formatter === formatKrwCurrency ? <CurrencyTooltip /> : <CountTooltip />} />
              <Bar dataKey="value" isAnimationActive={false} radius={[4, 4, 0, 0]}>
                {points.map((point) => (
                  <Cell fill={point.value < 0 ? "#b42318" : "#2e6140"} key={point.label} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

function monthlyProfit(rows: LedgerRow[]) {
  /** 매도일이 있는 원장 행만 월별로 묶어 표시손익 합계를 계산합니다. */

  const byMonth = new Map<string, number>();
  for (const row of rows) {
    if (!row.sellDate) {
      continue;
    }

    const label = row.sellDate.slice(2, 7).replace("-", ".");
    byMonth.set(label, (byMonth.get(label) ?? 0) + row.profitKrw);
  }

  return Array.from(byMonth.entries()).map(([label, value]) => ({ label, value }));
}

function openLotRateBuckets(rows: LedgerRow[], currencyCode: CurrencyCode) {
  /** 아직 매도되지 않은 open 로트를 매수환율 50원 단위 구간으로 집계합니다. */

  const openRows = rows.filter((row) => !row.sellDate);
  if (openRows.length === 0) {
    return [];
  }

  const buckets = new Map<string, number>();
  const bucketSize = currencyCode === "JPY" ? 10 : 50;
  for (const row of openRows) {
    const rate = Number(row.buyExchangeRate);
    const start = Math.floor(rate / bucketSize) * bucketSize;
    const label = `${formatKrwRate(start)}~${formatKrwRate(start + bucketSize - 1)}`;
    buckets.set(label, (buckets.get(label) ?? 0) + 1);
  }

  return Array.from(buckets.entries()).map(([label, value]) => ({ label, value }));
}

function openLotCountsByCurrency(ledgers: LedgerResponse[]) {
  /** 전체 보기에서 환율 구간 대신 통화별 open 로트 수를 보여주기 위한 막대 데이터를 만듭니다. */

  return ledgers.map((ledger) => ({
    label: ledger.summary.currencyCode,
    value: ledger.summary.openLotCount
  }));
}

function cumulativeProfitPoints(ledgers: LedgerResponse[]) {
  /** 통화별 원장 행을 날짜순으로 합쳐 전체/USD/JPY 누적수익 포인트로 변환합니다. */

  const soldRows = ledgers
    .flatMap((ledger) =>
      ledger.items
        .filter((row) => row.sellDate)
        .map((row) => ({
          row,
          currencyCode: ledger.summary.currencyCode,
          sellDate: row.sellDate ?? row.buyDate
        }))
    )
    .sort(
      (left, right) =>
        left.sellDate.localeCompare(right.sellDate) ||
        left.row.buyLotId - right.row.buyLotId ||
        (left.row.lotAllocationId ?? 0) - (right.row.lotAllocationId ?? 0)
    );

  const currencyTotals: Record<CurrencyCode, number> = { USD: 0, JPY: 0 };
  let total = 0;

  return soldRows.map(({ currencyCode, row, sellDate }) => {
    total += row.profitKrw;
    currencyTotals[currencyCode] = row.cumulativeProfitKrw;
    return {
      label: formatCompactDate(sellDate),
      total,
      USD: currencyTotals.USD || null,
      JPY: currencyTotals.JPY || null
    };
  });
}

function StatsContent() {
  /** FX 원장 데이터를 불러와 누적수익, 월별손익, open 로트 분포 차트로 변환합니다. */

  const [period, setPeriod] = useState("all");
  const [currencyCode, setCurrencyCode] = useState<StatsCurrencyCode>("ALL");
  const [data, setData] = useState<LedgerResponse[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    const load =
      currencyCode === "ALL"
        ? Promise.all(currencyOptions.map((option) => getLedger(period, option.code)))
        : getLedger(period, currencyCode).then((ledger) => [ledger]);

    load
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "통계 데이터를 불러오지 못했습니다.")
      );
  }, [period, currencyCode]);

  const stats = useMemo(() => {
    const ledgers = data ?? [];
    const rows = ledgers.flatMap((ledger) => ledger.items);
    const firstLedger = ledgers[0];
    return {
      cumulative: cumulativeProfitPoints(ledgers),
      monthly: monthlyProfit(rows),
      openBuckets:
        currencyCode === "ALL"
          ? openLotCountsByCurrency(ledgers)
          : openLotRateBuckets(firstLedger?.items ?? [], currencyCode)
    };
  }, [currencyCode, data]);

  const summary = useMemo(() => {
    const ledgers = data ?? [];
    const latestLedgerDate = ledgers
      .map((ledger) => ledger.summary.latestLedgerDate)
      .filter((value): value is string => Boolean(value))
      .sort()
      .at(-1) ?? null;

    return {
      latestLedgerDate,
      totalDisplayProfitKrw: ledgers.reduce((total, ledger) => total + ledger.summary.totalDisplayProfitKrw, 0),
      finalCumulativeProfitKrw: ledgers.reduce((total, ledger) => total + ledger.summary.finalCumulativeProfitKrw, 0),
      openAmounts: Object.fromEntries(
        ledgers.map((ledger) => [ledger.summary.currencyCode, ledger.summary.totalOpenUsdAmount])
      ) as Partial<Record<CurrencyCode, string>>
    };
  }, [data]);

  const selectedCurrency = currencyCode === "ALL" ? null : getCurrencyOption(currencyCode);

  return (
    <main className="content-page ledger-page">
      <section className="content-header content-header-actions">
        <div className="ledger-actions">
          <label className="period-select">
            보기
            <select value={currencyCode} onChange={(event) => setCurrencyCode(event.target.value as StatsCurrencyCode)}>
              {statsCurrencyOptions.map((option) => (
                <option key={option.code} value={option.code}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
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
        </div>
      </section>

      {error ? <p className="form-error">{error}</p> : null}
      {!data ? (
        <p>통계 데이터를 불러오는 중입니다.</p>
      ) : (
        <>
          <section className="ledger-summary">
            <div>
              <span>{selectedCurrency ? `환전가능 ${selectedCurrency.amountLabel}` : "환전가능 달러"}</span>
              <strong>
                {formatForeignCurrency(
                  selectedCurrency ? summary.openAmounts[selectedCurrency.code] ?? "0" : summary.openAmounts.USD ?? "0",
                  selectedCurrency?.code ?? "USD"
                )}
              </strong>
            </div>
            <div>
              <span>{selectedCurrency ? "마지막 기준일" : "환전가능 엔화"}</span>
              <strong>
                {selectedCurrency
                  ? summary.latestLedgerDate ? formatCompactDate(summary.latestLedgerDate) : ""
                  : formatForeignCurrency(summary.openAmounts.JPY ?? "0", "JPY")}
              </strong>
            </div>
            <div>
              <span>표시손익 합계</span>
              <strong>{formatKrwCurrency(summary.totalDisplayProfitKrw)}</strong>
            </div>
            <div>
              <span>최종 누적수익</span>
              <strong className="profit-strong">{formatKrwCurrency(summary.finalCumulativeProfitKrw)}</strong>
            </div>
          </section>

          <section className="stats-grid">
            <CumulativeProfitChart points={stats.cumulative} />
            <StatsBarChart
              emptyText="매도 기록이 없습니다."
              formatter={formatKrwCurrency}
              points={stats.monthly}
              subtitle="매도일 기준 월별 차익 합계"
              title="월별 실현손익"
            />
            <StatsBarChart
              emptyText="Open 로트가 없습니다."
              formatter={(value) => `${formatKrw(value)}건`}
              points={stats.openBuckets}
              subtitle={selectedCurrency ? "아직 매도되지 않은 매수환율 구간" : "통화별 현재 open 로트 수"}
              title={selectedCurrency ? `${selectedCurrency.label} Open 로트 환율 분포` : "통화별 Open 로트"}
            />
          </section>
        </>
      )}
    </main>
  );
}

export default function StatsPage() {
  /** FX 통계 화면 전체를 인증 가드로 보호합니다. */

  return (
    <AuthGuard>
      <StatsContent />
    </AuthGuard>
  );
}

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
import { formatCompactDate, formatKrw, formatKrwCurrency, formatKrwRate } from "../../../src/lib/format";
import { getLedger, type LedgerResponse, type LedgerRow } from "../../../src/lib/fx-api";

const periodOptions = [
  { value: "all", label: "전체" },
  { value: "1y", label: "최근 1년" },
  { value: "3y", label: "최근 3년" },
  { value: "5y", label: "최근 5년" },
  { value: "latest", label: "마지막 날짜만" }
];

type LinePoint = {
  /** 선형 차트에서 X축 라벨과 Y축 금액을 표현하는 점입니다. */
  label: string;
  value: number;
};

type BarPoint = {
  /** 막대 차트에서 구간/월 라벨과 집계값을 표현하는 점입니다. */
  label: string;
  value: number;
};

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

function CumulativeProfitChart({ points }: { points: LinePoint[] }) {
  /** 매도 allocation 순서에 따른 누적수익 흐름을 선형 차트로 표시합니다. */

  const lastPoint = points.at(-1);

  return (
    <div className="chart-card wide">
      <div className="chart-heading">
        <div>
          <h2>누적수익 추이</h2>
          <span>매도 allocation 기준 누적 흐름</span>
        </div>
        <strong>{lastPoint ? formatKrwCurrency(lastPoint.value) : "-"}</strong>
      </div>
      {points.length === 0 ? (
        <p className="empty-chart">매도 기록이 없습니다.</p>
      ) : (
        <div className="chart-canvas">
          <ResponsiveContainer height={300} width="100%">
            <LineChart data={points} margin={{ bottom: 8, left: 8, right: 20, top: 12 }}>
              <CartesianGrid stroke="#dce4dd" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="label" minTickGap={24} tick={{ fill: "#52705e", fontSize: 12 }} tickLine={false} />
              <YAxis
                tick={{ fill: "#52705e", fontSize: 12 }}
                tickFormatter={(value) => formatKrw(Number(value))}
                tickLine={false}
                width={82}
              />
              <Tooltip content={<CurrencyTooltip />} />
              <Line
                activeDot={{ r: 5 }}
                dataKey="value"
                dot={{ r: 3 }}
                isAnimationActive={false}
                stroke="#2e6140"
                strokeWidth={3}
                type="monotone"
              />
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

function openLotRateBuckets(rows: LedgerRow[]) {
  /** 아직 매도되지 않은 open 로트를 매수환율 50원 단위 구간으로 집계합니다. */

  const openRows = rows.filter((row) => !row.sellDate);
  if (openRows.length === 0) {
    return [];
  }

  const buckets = new Map<string, number>();
  for (const row of openRows) {
    const rate = Number(row.buyExchangeRate);
    const start = Math.floor(rate / 50) * 50;
    const label = `${formatKrwRate(start)}~${formatKrwRate(start + 49)}`;
    buckets.set(label, (buckets.get(label) ?? 0) + 1);
  }

  return Array.from(buckets.entries()).map(([label, value]) => ({ label, value }));
}

function cumulativeProfitPoints(rows: LedgerRow[]) {
  /** 매도 행의 누적수익 값을 차트 포인트로 변환합니다. */

  return rows
    .filter((row) => row.sellDate)
    .map((row) => ({
      label: formatCompactDate(row.sellDate ?? row.buyDate),
      value: row.cumulativeProfitKrw
    }));
}

function StatsContent() {
  /** FX 원장 데이터를 불러와 누적수익, 월별손익, open 로트 분포 차트로 변환합니다. */

  const [period, setPeriod] = useState("all");
  const [data, setData] = useState<LedgerResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    getLedger(period)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "통계 데이터를 불러오지 못했습니다.")
      );
  }, [period]);

  const stats = useMemo(() => {
    const rows = data?.items ?? [];
    return {
      cumulative: cumulativeProfitPoints(rows),
      monthly: monthlyProfit(rows),
      openBuckets: openLotRateBuckets(rows)
    };
  }, [data]);

  return (
    <main className="content-page ledger-page">
      <section className="content-header">
        <div>
          <p className="eyebrow">FX Analytics</p>
          <h1>FX 통계</h1>
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
        </div>
      </section>

      {error ? <p className="form-error">{error}</p> : null}
      {!data ? (
        <p>통계 데이터를 불러오는 중입니다.</p>
      ) : (
        <>
          <section className="ledger-summary">
            <div>
              <span>표시 행</span>
              <strong>{formatKrw(data.summary.visibleRows)}</strong>
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
              subtitle="아직 매도되지 않은 매수환율 구간"
              title="Open 로트 환율 분포"
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

"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AdminGuard } from "../../../../src/components/admin-guard";
import { AdminShell } from "../../../../src/components/admin-shell";
import { getUser, type AdminUserDetail } from "../../../../src/lib/admin-api";
import { formatDate, formatDateTime, formatKrw, formatNumber, formatUsd } from "../../../../src/lib/format";

function UserDetailContent() {
  const params = useParams<{ userId: string }>();
  const userId = Number(params.userId);
  const [user, setUser] = useState<AdminUserDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!Number.isFinite(userId)) {
      return;
    }

    getUser(userId)
      .then(setUser)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "사용자 상세를 불러오지 못했습니다.")
      );
  }, [userId]);

  return (
    <AdminShell>
      <main className="content-page">
        <Link className="back-link" href="/admin/users">
          사용자 목록
        </Link>
        {error ? <p className="form-error">{error}</p> : null}
        {!user ? (
          <p>사용자 상세를 불러오는 중입니다.</p>
        ) : (
          <>
            <section className="content-header">
              <div>
                <p className="eyebrow">User #{user.user_id}</p>
                <h1>{user.display_name}</h1>
              </div>
              <Link className="secondary-link" href={`/admin/fx/ledger?userId=${user.user_id}`}>
                FX 원장 보기
              </Link>
            </section>
            <section className="definition-grid">
              <div>
                <span>email</span>
                <strong>{user.email}</strong>
              </div>
              <div>
                <span>login_id</span>
                <strong>{user.login_id}</strong>
              </div>
              <div>
                <span>상태</span>
                <strong>{user.user_status}</strong>
              </div>
              <div>
                <span>roles</span>
                <strong>{user.roles.join(", ")}</strong>
              </div>
              <div>
                <span>기본 배분</span>
                <strong>{user.default_allocation_strategy}</strong>
              </div>
              <div>
                <span>생성일</span>
                <strong>{formatDateTime(user.created_at)}</strong>
              </div>
            </section>
            <section className="metric-grid">
              <div>
                <span>총 매수 원화</span>
                <strong>{formatKrw(user.fx_summary.total_buy_krw_amount)}</strong>
              </div>
              <div>
                <span>총 매수 USD</span>
                <strong>{formatUsd(user.fx_summary.total_buy_usd_amount)}</strong>
              </div>
              <div>
                <span>매수 lot</span>
                <strong>{formatNumber(user.fx_summary.buy_lot_count)}</strong>
              </div>
              <div>
                <span>open lot</span>
                <strong>{formatNumber(user.fx_summary.open_lot_count)}</strong>
              </div>
              <div>
                <span>매도 거래</span>
                <strong>{formatNumber(user.fx_summary.sell_transaction_count)}</strong>
              </div>
              <div>
                <span>event</span>
                <strong>{formatNumber(user.fx_summary.lot_event_count)}</strong>
              </div>
              <div>
                <span>실현손익</span>
                <strong>{formatKrw(user.fx_summary.total_real_profit_krw)}</strong>
              </div>
              <div>
                <span>표시손익</span>
                <strong>{formatKrw(user.fx_summary.total_display_profit_krw)}</strong>
              </div>
              <div>
                <span>최종 누적수익</span>
                <strong>{formatKrw(user.fx_summary.final_cumulative_profit_krw)}</strong>
              </div>
              <div>
                <span>마지막 원장일</span>
                <strong>
                  {user.fx_summary.latest_ledger_date
                    ? formatDate(user.fx_summary.latest_ledger_date)
                    : ""}
                </strong>
              </div>
              <div>
                <span>open USD</span>
                <strong>{formatUsd(user.fx_summary.open_usd_amount)}</strong>
              </div>
            </section>
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function UserDetailPage() {
  return (
    <AdminGuard>
      <UserDetailContent />
    </AdminGuard>
  );
}

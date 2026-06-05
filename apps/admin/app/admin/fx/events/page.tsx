"use client";

import { useEffect, useState } from "react";
import { AdminGuard } from "../../../../src/components/admin-guard";
import { AdminShell } from "../../../../src/components/admin-shell";
import { listLotEvents, type AdminLotEvent, type Paginated } from "../../../../src/lib/admin-api";
import { formatDateTime, formatNumber } from "../../../../src/lib/format";

function EventsContent() {
  const [userId, setUserId] = useState("");
  const [eventType, setEventType] = useState("");
  const [filters, setFilters] = useState({ userId: "", eventType: "" });
  const [data, setData] = useState<Paginated<AdminLotEvent> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listLotEvents(filters)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "이벤트 로그를 불러오지 못했습니다.")
      );
  }, [filters]);

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">FX Events</p>
            <h1>fx_lot_events</h1>
          </div>
          <form
            className="inline-form"
            onSubmit={(event) => {
              event.preventDefault();
              setFilters({ userId, eventType });
            }}
          >
            <label>
              user_id
              <input value={userId} onChange={(event) => setUserId(event.target.value)} />
            </label>
            <label>
              event_type
              <input value={eventType} onChange={(event) => setEventType(event.target.value)} />
            </label>
            <button className="primary-button" type="submit">
              조회
            </button>
          </form>
        </section>
        {error ? <p className="form-error">{error}</p> : null}
        {!data ? (
          <p>이벤트 로그를 불러오는 중입니다.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>user</th>
                    <th>type</th>
                    <th>status</th>
                    <th>root</th>
                    <th>sell</th>
                    <th>allocation</th>
                    <th>created</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((event) => (
                    <tr key={event.lot_event_id}>
                      <td>{event.lot_event_id}</td>
                      <td>{event.user_id}</td>
                      <td>{event.event_type}</td>
                      <td>{event.event_status}</td>
                      <td>{event.root_buy_lot_id}</td>
                      <td>{event.sell_transaction_id}</td>
                      <td>{event.lot_allocation_id}</td>
                      <td>{formatDateTime(event.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="pagination-summary">
              page {data.page} / size {data.size} / total {formatNumber(data.total_count)}
            </p>
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function EventsPage() {
  return (
    <AdminGuard>
      <EventsContent />
    </AdminGuard>
  );
}

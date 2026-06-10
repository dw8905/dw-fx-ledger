"use client";

import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "../../../../src/components/admin-guard";
import { AdminShell } from "../../../../src/components/admin-shell";
import { Pagination } from "../../../../src/components/pagination";
import { listLotEvents, type AdminLotEvent, type Paginated } from "../../../../src/lib/admin-api";
import { formatDateTime } from "../../../../src/lib/format";

type EventFilters = {
  /** FX 이벤트 로그 화면에서 지원하는 user/event/transaction/lot 필터입니다. */
  userId: string;
  eventType: string;
  sellTransactionId: string;
  rootBuyLotId: string;
};

const emptyFilters: EventFilters = {
  userId: "",
  eventType: "",
  sellTransactionId: "",
  rootBuyLotId: ""
};

const eventTypes = [
  "sell_transaction_created",
  "lot_split",
  "sell_transaction_cancelled",
  "lot_restored"
];

function EventsContent() {
  /** FX 이벤트 로그의 검색 필터, 페이지네이션, 조회 결과를 관리합니다. */

  const [draftFilters, setDraftFilters] = useState<EventFilters>(emptyFilters);
  const [filters, setFilters] = useState<EventFilters>(emptyFilters);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<Paginated<AdminLotEvent> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listLotEvents({
      page,
      size,
      userId: filters.userId,
      eventType: filters.eventType,
      sellTransactionId: filters.sellTransactionId,
      rootBuyLotId: filters.rootBuyLotId
    })
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "이벤트 로그를 불러오지 못했습니다.")
      );
  }, [filters, page, size]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 이벤트 로그 필터 입력값을 실제 조회 조건으로 확정합니다. */

    event.preventDefault();
    setPage(1);
    setFilters(draftFilters);
  }

  function resetFilters() {
    /** 이벤트 로그 필터를 비우고 첫 페이지를 다시 조회합니다. */

    setDraftFilters(emptyFilters);
    setFilters(emptyFilters);
    setPage(1);
  }

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">FX Events</p>
            <h1>fx_lot_events</h1>
          </div>
        </section>
        <form className="filter-bar" onSubmit={handleSubmit}>
          <label>
            user_id
            <input
              value={draftFilters.userId}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, userId: event.target.value }))
              }
            />
          </label>
          <label>
            event_type
            <select
              value={draftFilters.eventType}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, eventType: event.target.value }))
              }
            >
              <option value="">전체</option>
              {eventTypes.map((eventType) => (
                <option key={eventType} value={eventType}>
                  {eventType}
                </option>
              ))}
            </select>
          </label>
          <label>
            sell_transaction_id
            <input
              value={draftFilters.sellTransactionId}
              onChange={(event) =>
                setDraftFilters((current) => ({
                  ...current,
                  sellTransactionId: event.target.value
                }))
              }
            />
          </label>
          <label>
            root_buy_lot_id
            <input
              value={draftFilters.rootBuyLotId}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, rootBuyLotId: event.target.value }))
              }
            />
          </label>
          <button className="primary-button" type="submit">
            검색
          </button>
          <button className="secondary-button" type="button" onClick={resetFilters}>
            초기화
          </button>
        </form>
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
            <Pagination
              page={data.page}
              size={data.size}
              totalCount={data.total_count}
              totalPages={data.total_pages}
              onPageChange={setPage}
              onSizeChange={(nextSize) => {
                setSize(nextSize);
                setPage(1);
              }}
            />
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function EventsPage() {
  /** 관리자 FX 이벤트 로그 화면 전체를 admin 권한 가드로 보호합니다. */

  return (
    <AdminGuard>
      <EventsContent />
    </AdminGuard>
  );
}

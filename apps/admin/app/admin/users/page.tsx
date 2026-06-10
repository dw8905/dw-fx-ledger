"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { Pagination } from "../../../src/components/pagination";
import { listUsers, type AdminUserListItem, type Paginated } from "../../../src/lib/admin-api";
import { formatDateTime } from "../../../src/lib/format";

type UserFilters = {
  /** 사용자 목록 검색 폼에서 확정/임시 상태로 나누어 관리하는 필터입니다. */
  keyword: string;
  userStatus: string;
  role: string;
};

const emptyFilters: UserFilters = {
  keyword: "",
  userStatus: "",
  role: ""
};

function UsersContent() {
  /** 사용자 목록의 검색/필터/페이지네이션 상태와 조회 결과를 관리합니다. */

  const [draftFilters, setDraftFilters] = useState<UserFilters>(emptyFilters);
  const [filters, setFilters] = useState<UserFilters>(emptyFilters);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<Paginated<AdminUserListItem> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    listUsers({
      page,
      size,
      keyword: filters.keyword,
      userStatus: filters.userStatus,
      role: filters.role
    })
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "사용자 목록을 불러오지 못했습니다.")
      );
  }, [filters, page, size]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    /** 검색 폼의 임시 입력값을 실제 조회 필터로 확정하고 첫 페이지로 이동합니다. */

    event.preventDefault();
    setPage(1);
    setFilters(draftFilters);
  }

  function resetFilters() {
    /** 사용자 목록 필터를 초기값으로 되돌리고 첫 페이지를 다시 조회합니다. */

    setDraftFilters(emptyFilters);
    setFilters(emptyFilters);
    setPage(1);
  }

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Users</p>
            <h1>사용자 목록</h1>
          </div>
        </section>
        <form className="filter-bar" onSubmit={handleSubmit}>
          <label>
            검색
            <input
              placeholder="email, login_id, 이름"
              value={draftFilters.keyword}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, keyword: event.target.value }))
              }
            />
          </label>
          <label>
            상태
            <select
              value={draftFilters.userStatus}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, userStatus: event.target.value }))
              }
            >
              <option value="">전체</option>
              <option value="active">active</option>
              <option value="locked">locked</option>
              <option value="withdrawn">withdrawn</option>
            </select>
          </label>
          <label>
            role
            <select
              value={draftFilters.role}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, role: event.target.value }))
              }
            >
              <option value="">전체</option>
              <option value="user">user</option>
              <option value="admin">admin</option>
            </select>
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
          <p>사용자를 불러오는 중입니다.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>email</th>
                    <th>login_id</th>
                    <th>이름</th>
                    <th>상태</th>
                    <th>roles</th>
                    <th>생성일</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((user) => (
                    <tr key={user.user_id}>
                      <td>{user.user_id}</td>
                      <td>
                        <Link href={`/admin/users/${user.user_id}`}>{user.email}</Link>
                      </td>
                      <td>{user.login_id}</td>
                      <td>{user.display_name}</td>
                      <td>{user.user_status}</td>
                      <td>{user.roles.join(", ")}</td>
                      <td>{formatDateTime(user.created_at)}</td>
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

export default function UsersPage() {
  /** 관리자 사용자 목록 화면 전체를 admin 권한 가드로 보호합니다. */

  return (
    <AdminGuard>
      <UsersContent />
    </AdminGuard>
  );
}

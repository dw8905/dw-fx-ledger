"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { listUsers, type AdminUserListItem, type Paginated } from "../../../src/lib/admin-api";
import { formatDateTime, formatNumber } from "../../../src/lib/format";

function UsersContent() {
  const [data, setData] = useState<Paginated<AdminUserListItem> | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listUsers(1, 50)
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "사용자 목록을 불러오지 못했습니다.")
      );
  }, []);

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Users</p>
            <h1>사용자 목록</h1>
          </div>
        </section>
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
            <p className="pagination-summary">
              page {data.page} / size {data.size} / total {formatNumber(data.total_count)}
            </p>
          </>
        )}
      </main>
    </AdminShell>
  );
}

export default function UsersPage() {
  return (
    <AdminGuard>
      <UsersContent />
    </AdminGuard>
  );
}

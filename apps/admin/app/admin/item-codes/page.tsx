"use client";

import { FormEvent, useEffect, useState } from "react";
import { AdminGuard } from "../../../src/components/admin-guard";
import { AdminShell } from "../../../src/components/admin-shell";
import { Pagination } from "../../../src/components/pagination";
import {
  createItemCode,
  deactivateItemCode,
  listItemCodes,
  updateItemCode,
  type AdminItemCode,
  type Paginated
} from "../../../src/lib/admin-api";
import { formatDateTime } from "../../../src/lib/format";

type Filters = {
  keyword: string;
  isActive: string;
};

type FormState = {
  item_name: string;
  memo: string;
  is_active: boolean;
};

const initialFilters: Filters = {
  keyword: "",
  isActive: ""
};

const initialForm: FormState = {
  item_name: "",
  memo: "",
  is_active: true
};

function ItemCodesContent() {
  const [draftFilters, setDraftFilters] = useState<Filters>(initialFilters);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [form, setForm] = useState<FormState>(initialForm);
  const [editing, setEditing] = useState<AdminItemCode | null>(null);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState<Paginated<AdminItemCode> | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setError("");
    listItemCodes({
      page,
      size,
      keyword: filters.keyword,
      isActive: filters.isActive
    })
      .then(setData)
      .catch((caughtError) =>
        setError(caughtError instanceof Error ? caughtError.message : "자산 코드를 불러오지 못했습니다.")
      );
  }, [filters, page, size]);

  function handleFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setFilters(draftFilters);
  }

  function resetFilters() {
    setDraftFilters(initialFilters);
    setFilters(initialFilters);
    setPage(1);
  }

  function startEdit(code: AdminItemCode) {
    setEditing(code);
    setForm({
      item_name: code.item_name,
      memo: code.memo ?? "",
      is_active: code.is_active
    });
  }

  function resetForm() {
    setEditing(null);
    setForm(initialForm);
  }

  async function reload() {
    const next = await listItemCodes({
      page,
      size,
      keyword: filters.keyword,
      isActive: filters.isActive
    });
    setData(next);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSaving(true);
    try {
      const payload = {
        item_name: form.item_name,
        memo: form.memo || undefined,
        is_active: form.is_active
      };
      if (editing) {
        await updateItemCode(editing.item_code_id, payload);
      } else {
        await createItemCode(payload);
      }
      resetForm();
      await reload();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "자산 코드 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(code: AdminItemCode) {
    if (!window.confirm(`${code.item_name} 코드를 비활성화할까요? 기존 거래 기록은 유지됩니다.`)) {
      return;
    }

    setError("");
    try {
      await deactivateItemCode(code.item_code_id);
      await reload();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "자산 코드 비활성화에 실패했습니다.");
    }
  }

  return (
    <AdminShell>
      <main className="content-page">
        <section className="content-header">
          <div>
            <p className="eyebrow">Asset Codes</p>
            <h1>자산 코드 관리</h1>
          </div>
        </section>

        <form className="filter-bar" onSubmit={handleFilterSubmit}>
          <label>
            검색
            <input
              placeholder="자산명"
              value={draftFilters.keyword}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, keyword: event.target.value }))
              }
            />
          </label>
          <label>
            상태
            <select
              value={draftFilters.isActive}
              onChange={(event) =>
                setDraftFilters((current) => ({ ...current, isActive: event.target.value }))
              }
            >
              <option value="">전체</option>
              <option value="true">활성</option>
              <option value="false">비활성</option>
            </select>
          </label>
          <button className="primary-button" type="submit">
            검색
          </button>
          <button className="secondary-button" type="button" onClick={resetFilters}>
            초기화
          </button>
        </form>

        <form className="filter-bar" onSubmit={(event) => void handleSubmit(event)}>
          <label>
            자산명
            <input
              required
              maxLength={120}
              value={form.item_name}
              onChange={(event) => setForm((current) => ({ ...current, item_name: event.target.value }))}
            />
          </label>
          <label>
            메모
            <input
              value={form.memo}
              onChange={(event) => setForm((current) => ({ ...current, memo: event.target.value }))}
            />
          </label>
          <label className="check-control">
            <input
              checked={form.is_active}
              type="checkbox"
              onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
            />
            활성
          </label>
          <button className="primary-button" disabled={saving} type="submit">
            {saving ? "저장 중" : editing ? "수정" : "등록"}
          </button>
          {editing ? (
            <button className="secondary-button" type="button" onClick={resetForm}>
              취소
            </button>
          ) : null}
        </form>

        {error ? <p className="form-error">{error}</p> : null}
        {!data ? (
          <p>자산 코드를 불러오는 중입니다.</p>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>코드</th>
                    <th>자산명</th>
                    <th>상태</th>
                    <th>메모</th>
                    <th>수정일</th>
                    <th>작업</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((code) => (
                    <tr key={code.item_code_id}>
                      <td>{code.item_code_id}</td>
                      <td>{code.item_code}</td>
                      <td>{code.item_name}</td>
                      <td>{code.is_active ? "활성" : "비활성"}</td>
                      <td>{code.memo ?? "-"}</td>
                      <td>{formatDateTime(code.updated_at)}</td>
                      <td>
                        <div className="table-actions">
                          <button className="secondary-button" type="button" onClick={() => startEdit(code)}>
                            수정
                          </button>
                          <button
                            className="secondary-button"
                            disabled={!code.is_active}
                            type="button"
                            onClick={() => void handleDeactivate(code)}
                          >
                            비활성
                          </button>
                        </div>
                      </td>
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

export default function ItemCodesPage() {
  return (
    <AdminGuard>
      <ItemCodesContent />
    </AdminGuard>
  );
}

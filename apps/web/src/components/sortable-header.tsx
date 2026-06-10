"use client";

/** 정렬 헤더가 표현할 수 있는 정렬 방향입니다. */
export type SortOrder = "asc" | "desc" | null;

type SortableHeaderProps = {
  /** 테이블 헤더에서 어떤 필드가 현재 정렬 대상인지 판단하는 데 필요한 값입니다. */
  label: string;
  field: string;
  sortBy: string | null;
  sortOrder: SortOrder;
  onSort: (field: string) => void;
};

export function SortableHeader({ label, field, sortBy, sortOrder, onSort }: SortableHeaderProps) {
  /** 클릭 가능한 정렬 헤더와 현재 정렬 방향 마커를 표시합니다. */

  const active = sortBy === field;
  const marker = active ? (sortOrder === "asc" ? "▲" : sortOrder === "desc" ? "▼" : "↕") : "↕";

  return (
    <button className="sort-button" type="button" onClick={() => onSort(field)}>
      {label} {marker}
    </button>
  );
}

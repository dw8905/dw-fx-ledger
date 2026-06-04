"use client";

export type SortOrder = "asc" | "desc" | null;

type SortableHeaderProps = {
  label: string;
  field: string;
  sortBy: string | null;
  sortOrder: SortOrder;
  onSort: (field: string) => void;
};

export function SortableHeader({ label, field, sortBy, sortOrder, onSort }: SortableHeaderProps) {
  const active = sortBy === field;
  const marker = active ? (sortOrder === "asc" ? "▲" : sortOrder === "desc" ? "▼" : "↕") : "↕";

  return (
    <button className="sort-button" type="button" onClick={() => onSort(field)}>
      {label} {marker}
    </button>
  );
}

type PaginationProps = {
  page: number;
  size: number;
  totalCount: number;
  onPageChange: (page: number) => void;
  onSizeChange?: (size: number) => void;
  sizeOptions?: number[];
};

export function Pagination({
  page,
  size,
  totalCount,
  onPageChange,
  onSizeChange,
  sizeOptions = [10, 20, 50]
}: PaginationProps) {
  const totalPages = Math.max(Math.ceil(totalCount / size), 1);

  return (
    <div className="pagination">
      <span>
        page {page} / {totalPages} · total {totalCount}
      </span>
      <div className="pagination-actions">
        <button
          className="secondary-button"
          disabled={page <= 1}
          type="button"
          onClick={() => onPageChange(page - 1)}
        >
          이전
        </button>
        <button
          className="secondary-button"
          disabled={page >= totalPages}
          type="button"
          onClick={() => onPageChange(page + 1)}
        >
          다음
        </button>
        {onSizeChange ? (
          <label className="pagination-size">
            size
            <select value={size} onChange={(event) => onSizeChange(Number(event.target.value))}>
              {sizeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>
    </div>
  );
}

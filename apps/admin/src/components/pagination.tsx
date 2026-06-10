import { formatNumber } from "../lib/format";

const pageSizeOptions = [10, 20, 50];

type PaginationProps = {
  /** 관리자 목록 화면들이 공통으로 쓰는 현재 페이지/전체 페이지/size 제어값입니다. */
  page: number;
  size: number;
  totalCount: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  onSizeChange: (size: number) => void;
};

export function Pagination({
  page,
  size,
  totalCount,
  totalPages,
  onPageChange,
  onSizeChange
}: PaginationProps) {
  /** 관리자 테이블 하단의 이전/다음 버튼과 page size 선택 UI를 렌더링합니다. */

  const safeTotalPages = Math.max(totalPages, 1);

  return (
    <div className="pagination">
      <div>
        page {formatNumber(page)} / {formatNumber(safeTotalPages)} · total{" "}
        {formatNumber(totalCount)}
      </div>
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
          disabled={page >= safeTotalPages}
          type="button"
          onClick={() => onPageChange(page + 1)}
        >
          다음
        </button>
        <label>
          size
          <select
            value={size}
            onChange={(event) => onSizeChange(Number(event.target.value))}
          >
            {pageSizeOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}

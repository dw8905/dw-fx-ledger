"use client";

import Link from "next/link";

export type SectionTabItem<T extends string = string> = {
  /** 상위 메뉴 아래에서 재사용하는 탭의 식별자, 라벨, 선택 링크입니다. */
  id: T;
  label: string;
  href?: string;
};

export function SectionTabs<T extends string>({
  activeId,
  ariaLabel,
  items,
  onSelect
}: {
  activeId: T;
  ariaLabel: string;
  items: Array<SectionTabItem<T>>;
  onSelect?: (id: T) => void;
}) {
  /** 링크형 탭과 버튼형 탭을 같은 디자인 규격으로 렌더링합니다. */

  return (
    <nav className="section-tabs" aria-label={ariaLabel}>
      {items.map((item) =>
        item.href ? (
          <Link aria-current={activeId === item.id ? "page" : undefined} href={item.href} key={item.id}>
            {item.label}
          </Link>
        ) : (
          <button
            aria-current={activeId === item.id ? "page" : undefined}
            key={item.id}
            type="button"
            onClick={() => onSelect?.(item.id)}
          >
            {item.label}
          </button>
        )
      )}
    </nav>
  );
}

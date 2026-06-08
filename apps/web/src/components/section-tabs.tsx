"use client";

import Link from "next/link";

export type SectionTabItem<T extends string = string> = {
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

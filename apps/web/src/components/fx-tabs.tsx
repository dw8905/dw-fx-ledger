"use client";

import { usePathname } from "next/navigation";
import { SectionTabs, type SectionTabItem } from "./section-tabs";

/** FX 상위 메뉴 아래에서 사용할 하위 탭 식별자입니다. */
export type FxTab = "buy" | "sell" | "ledger" | "stats" | "lab";

const tabs: Array<SectionTabItem<FxTab>> = [
  { id: "buy", href: "/fx/buy-lots", label: "매수" },
  { id: "sell", href: "/fx/sell-transactions", label: "매도" },
  { id: "ledger", href: "/fx/ledger", label: "원장" },
  { id: "stats", href: "/fx/stats", label: "통계" },
  { id: "lab", href: "/fx/dev-lab", label: "Lab" }
];

function getActiveFxTab(pathname: string): FxTab {
  /** 현재 URL 경로를 FX 하위 탭 식별자로 변환합니다. */

  if (pathname.startsWith("/fx/sell-transactions")) {
    return "sell";
  }
  if (pathname.startsWith("/fx/ledger")) {
    return "ledger";
  }
  if (pathname.startsWith("/fx/stats")) {
    return "stats";
  }
  if (pathname.startsWith("/fx/dev-lab")) {
    return "lab";
  }
  return "buy";
}

export function FxTabs({ active }: { active?: FxTab }) {
  /** FX 메뉴 아래의 매수/매도/원장/통계/Lab 탭을 공통 탭 디자인으로 표시합니다. */

  const pathname = usePathname();
  return <SectionTabs activeId={active ?? getActiveFxTab(pathname)} ariaLabel="FX 기능" items={tabs} />;
}

"use client";

import { usePathname } from "next/navigation";
import { SectionTabs, type SectionTabItem } from "./section-tabs";

export type FxTab = "buy" | "sell" | "ledger" | "stats" | "lab";

const tabs: Array<SectionTabItem<FxTab>> = [
  { id: "buy", href: "/fx/buy-lots", label: "매수" },
  { id: "sell", href: "/fx/sell-transactions", label: "매도" },
  { id: "ledger", href: "/fx/ledger", label: "원장" },
  { id: "stats", href: "/fx/stats", label: "통계" },
  { id: "lab", href: "/fx/dev-lab", label: "Lab" }
];

function getActiveFxTab(pathname: string): FxTab {
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
  const pathname = usePathname();
  return <SectionTabs activeId={active ?? getActiveFxTab(pathname)} ariaLabel="FX 기능" items={tabs} />;
}

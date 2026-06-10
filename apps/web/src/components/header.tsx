"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useAuth } from "../context/auth-context";

function currentItemLabel(tab: string | null) {
  /** 자산관리 tab 쿼리값을 브레드크럼에 보여줄 한국어 하위 메뉴명으로 바꿉니다. */

  if (tab === "sell") {
    return "매도";
  }
  if (tab === "inventory") {
    return "자산별 재고관리";
  }
  return "매수";
}

function currentSection(pathname: string, itemTab: string | null) {
  /** 현재 경로를 상단 브레드크럼의 상위/하위 메뉴 정보로 변환합니다. */

  if (pathname.startsWith("/fx/buy-lots")) {
    return { group: "FX", label: "매수" };
  }
  if (pathname.startsWith("/fx/sell-transactions")) {
    return { group: "FX", label: "매도" };
  }
  if (pathname.startsWith("/fx/ledger")) {
    return { group: "FX", label: "원장" };
  }
  if (pathname.startsWith("/fx/stats")) {
    return { group: "FX", label: "통계" };
  }
  if (pathname.startsWith("/fx/dev-lab")) {
    return { group: "FX", label: "Lab" };
  }
  if (pathname.startsWith("/fx")) {
    return { group: "FX", label: "매수" };
  }
  if (pathname.startsWith("/item-trades")) {
    return { group: "자산관리", label: currentItemLabel(itemTab) };
  }
  if (pathname.startsWith("/posts")) {
    return { group: "게시판", label: null };
  }
  return null;
}

export function Header() {
  /** 모든 웹 화면 상단에 고정되는 브랜드, 브레드크럼, 로그인 메뉴를 렌더링합니다. */

  const { status, user, logout } = useAuth();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const section = currentSection(pathname, searchParams.get("tab"));

  return (
    <header className="app-header">
      <div className="brand-breadcrumb" aria-label="현재 위치">
        <Link className="brand" href="/">
          DW FX Ledger
        </Link>
        {section ? (
          <>
            <span aria-hidden="true">&gt;</span>
            <Link href={section.group === "FX" ? "/fx" : section.group === "자산관리" ? "/item-trades" : "/posts"}>
              {section.group}
            </Link>
            {section.label ? (
              <>
                <span aria-hidden="true">&gt;</span>
                <span>{section.label}</span>
              </>
            ) : null}
          </>
        ) : null}
      </div>
      <nav className="header-nav" aria-label="사용자 메뉴">
        <Link href="/posts">게시판</Link>
        <Link href="/fx">FX</Link>
        <Link href="/item-trades">자산관리</Link>
        {status === "authenticated" ? (
          <>
            <span className="user-name">{user?.displayName}</span>
            <button className="link-button" type="button" onClick={() => void logout()}>
              로그아웃
            </button>
          </>
        ) : (
          <>
            <Link href="/login">로그인</Link>
            <Link href="/register">회원가입</Link>
          </>
        )}
      </nav>
    </header>
  );
}

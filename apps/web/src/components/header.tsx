"use client";

import Link from "next/link";
import { useAuth } from "../context/auth-context";

export function Header() {
  const { status, user, logout } = useAuth();

  return (
    <header className="app-header">
      <Link className="brand" href="/">
        DW FX Ledger
      </Link>
      <nav className="header-nav" aria-label="사용자 메뉴">
        <Link href="/posts">게시판</Link>
        <Link href="/fx/buy-lots">FX 매수</Link>
        <Link href="/fx/sell-transactions">FX 매도</Link>
        <Link href="/fx/ledger">FX 원장</Link>
        <Link href="/fx/dev-lab">FX Lab</Link>
        <Link href="/item-trades">아이템</Link>
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

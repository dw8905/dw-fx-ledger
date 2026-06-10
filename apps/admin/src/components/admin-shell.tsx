"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { type ReactNode } from "react";
import { useAuth } from "../context/auth-context";

const navItems = [
  { href: "/admin/users", label: "사용자" },
  { href: "/admin/posts", label: "게시글" },
  { href: "/admin/item-codes", label: "자산 코드" },
  { href: "/admin/fx/ledger", label: "FX 원장" },
  { href: "/admin/fx/events", label: "FX 이벤트" }
];

export function AdminShell({ children }: { children: ReactNode }) {
  /** 관리자 사이드바, 현재 메뉴 표시, 로그아웃 버튼을 모든 관리자 화면에 제공합니다. */

  const pathname = usePathname();
  const { logout, user } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/admin/users">
          DW Admin
        </Link>
        <nav>
          {navItems.map((item) => (
            <Link
              aria-current={pathname.startsWith(item.href) ? "page" : undefined}
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span>{user?.displayName}</span>
          <button className="text-button" onClick={() => void logout()} type="button">
            로그아웃
          </button>
        </div>
      </aside>
      {children}
    </div>
  );
}

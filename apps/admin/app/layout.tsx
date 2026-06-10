import type { Metadata } from "next";
import { AuthProvider } from "../src/context/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "DW FX Ledger Admin",
  description: "Administration app for DW FX Ledger"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  /** 관리자 앱 전체를 AuthProvider로 감싸 인증 상태를 공유하게 합니다. */

  return (
    <html lang="ko">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

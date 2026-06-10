import type { Metadata } from "next";
import { Suspense } from "react";
import { Header } from "../src/components/header";
import { AuthProvider } from "../src/context/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: "DW FX Ledger",
  description: "Foreign exchange lot management service"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  /** 전체 웹 앱을 AuthProvider와 공통 Header로 감싸는 최상위 레이아웃입니다. */

  return (
    <html lang="ko">
      <body>
        <AuthProvider>
          <Suspense fallback={null}>
            <Header />
          </Suspense>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}

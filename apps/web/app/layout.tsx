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

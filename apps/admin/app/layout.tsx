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
  return (
    <html lang="ko">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}

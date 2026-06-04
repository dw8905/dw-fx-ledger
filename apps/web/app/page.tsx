"use client";

import { serviceName } from "@dw-fx-ledger/shared";
import { AuthGuard } from "../src/components/auth-guard";
import { useAuth } from "../src/context/auth-context";

function HomeContent() {
  const { user } = useAuth();

  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Web</p>
        <h1>{serviceName}</h1>
        <p>{user?.displayName}님, 외화 환전 로트 관리 서비스를 시작할 준비가 됐습니다.</p>
      </section>
    </main>
  );
}

export default function HomePage() {
  return (
    <AuthGuard>
      <HomeContent />
    </AuthGuard>
  );
}

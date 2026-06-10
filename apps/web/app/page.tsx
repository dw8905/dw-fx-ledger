"use client";

import { serviceName } from "@dw-fx-ledger/shared";
import { AuthGuard } from "../src/components/auth-guard";
import { useAuth } from "../src/context/auth-context";

function HomeContent() {
  /** 로그인 후 첫 화면에서 서비스명과 사용자 환영 문구를 표시합니다. */

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
  /** 홈 화면은 인증된 사용자만 볼 수 있도록 AuthGuard로 감쌉니다. */

  return (
    <AuthGuard>
      <HomeContent />
    </AuthGuard>
  );
}

import { serviceName } from "@dw-fx-ledger/shared";

export default function HomePage() {
  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Web</p>
        <h1>{serviceName}</h1>
        <p>외화 환전 로트 관리 및 환차익 계산 서비스를 위한 사용자 앱입니다.</p>
      </section>
    </main>
  );
}

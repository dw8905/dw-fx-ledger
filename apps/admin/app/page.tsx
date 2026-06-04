import { serviceName } from "@dw-fx-ledger/shared";

export default function AdminHomePage() {
  return (
    <main className="page">
      <section className="panel">
        <p className="eyebrow">Admin</p>
        <h1>{serviceName} Admin</h1>
        <p>운영 관리를 위한 관리자 앱입니다.</p>
      </section>
    </main>
  );
}

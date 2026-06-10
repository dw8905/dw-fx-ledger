import type { ReactNode } from "react";
import { FxTabs } from "../../src/components/fx-tabs";

export default function FxLayout({ children }: { children: ReactNode }) {
  /** FX 하위 화면들이 공통 탭을 공유하도록 감싸는 레이아웃입니다. */

  return (
    <>
      <div className="section-tabs-frame">
        <FxTabs />
      </div>
      {children}
    </>
  );
}

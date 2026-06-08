import type { ReactNode } from "react";
import { FxTabs } from "../../src/components/fx-tabs";

export default function FxLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <div className="section-tabs-frame">
        <FxTabs />
      </div>
      {children}
    </>
  );
}

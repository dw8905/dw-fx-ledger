import { redirect } from "next/navigation";

export default function FxPage() {
  /** FX 상위 메뉴 접근 시 기본 탭인 매수 로트 목록으로 보냅니다. */

  redirect("/fx/buy-lots");
}

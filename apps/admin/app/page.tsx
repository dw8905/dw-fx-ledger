import { redirect } from "next/navigation";

export default function AdminHomePage() {
  /** 관리자 루트 접근 시 기본 화면인 사용자 목록으로 이동합니다. */

  redirect("/admin/users");
}

import { redirect } from "next/navigation";

/**
 * 旧スクリーナー管理ページ → /admin にリダイレクト
 */
export default function AdminScreenerPage() {
  redirect("/admin");
}

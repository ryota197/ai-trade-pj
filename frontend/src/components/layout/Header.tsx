import Link from "next/link";

/**
 * ナビゲーションリンク
 */
const navLinks = [
  { href: "/", label: "ダッシュボード" },
  { href: "/screener", label: "スクリーナー" },
  { href: "/portfolio", label: "ポートフォリオ" },
];

/**
 * アプリケーションヘッダー
 */
export function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <Link href="/" className="hover:opacity-80 transition-opacity">
              <h1 className="text-xl font-bold text-foreground">AI Trade App</h1>
            </Link>
            <p className="text-sm text-muted-foreground">
              CAN-SLIM投資支援アプリケーション
            </p>
          </div>
          <nav className="flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
}

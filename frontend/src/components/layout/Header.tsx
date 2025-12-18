/**
 * アプリケーションヘッダー
 */
export function Header() {
  return (
    <header className="border-b border-border bg-card">
      <div className="mx-auto max-w-7xl px-4 py-4">
        <h1 className="text-xl font-bold text-foreground">AI Trade App</h1>
        <p className="text-sm text-muted-foreground">
          CAN-SLIM投資支援アプリケーション
        </p>
      </div>
    </header>
  );
}

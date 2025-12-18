import { getHealth } from "@/lib/api";

export default async function Home() {
  let healthStatus = { status: "unknown", database: "unknown" };
  let error: string | null = null;

  try {
    const response = await getHealth();
    if (response.success) {
      healthStatus = response.data;
    }
  } catch (e) {
    error = e instanceof Error ? e.message : "接続エラー";
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-900">
      {/* Header */}
      <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-950">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
            AI Trade App
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            CAN-SLIM投資支援アプリケーション
          </p>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* Status Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          {/* API Status */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              API Status
            </h2>
            <div className="mt-2 flex items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full ${
                  error
                    ? "bg-red-500"
                    : healthStatus.status === "ok"
                      ? "bg-green-500"
                      : "bg-yellow-500"
                }`}
              />
              <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {error ? "Error" : healthStatus.status.toUpperCase()}
              </span>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-500">{error}</p>
            )}
          </div>

          {/* Database Status */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              Database
            </h2>
            <div className="mt-2 flex items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full ${
                  healthStatus.database === "connected"
                    ? "bg-green-500"
                    : "bg-red-500"
                }`}
              />
              <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {healthStatus.database === "connected"
                  ? "Connected"
                  : "Disconnected"}
              </span>
            </div>
          </div>

          {/* Phase */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h2 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
              Current Phase
            </h2>
            <div className="mt-2">
              <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                Phase 1
              </span>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                基盤構築
              </p>
            </div>
          </div>
        </div>

        {/* Module Cards */}
        <h2 className="mt-8 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Modules
        </h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {/* Market Module */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h3 className="font-medium text-zinc-900 dark:text-zinc-100">
              Market Module
            </h3>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              マーケット状態の判定・可視化
            </p>
            <span className="mt-4 inline-block rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              Coming Soon
            </span>
          </div>

          {/* Screener Module */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h3 className="font-medium text-zinc-900 dark:text-zinc-100">
              Screener Module
            </h3>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              CAN-SLIM条件スクリーニング
            </p>
            <span className="mt-4 inline-block rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              Coming Soon
            </span>
          </div>

          {/* Portfolio Module */}
          <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-950">
            <h3 className="font-medium text-zinc-900 dark:text-zinc-100">
              Portfolio Module
            </h3>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              ウォッチリスト・ペーパートレード
            </p>
            <span className="mt-4 inline-block rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
              Coming Soon
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

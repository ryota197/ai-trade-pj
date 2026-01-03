import { Header } from "@/components/layout/Header";
import { StatusCard } from "@/components/ui/StatusCard";
import { ModuleCard } from "@/components/ui/ModuleCard";
import type { ApiResponse, HealthResponse } from "@/types/api";

import { MarketDashboard } from "./_components/MarketDashboard";

/**
 * ヘルスチェック取得
 * Note: サーバーコンポーネントから直接バックエンドを呼び出す（開発用）
 */
async function getHealth(): Promise<ApiResponse<HealthResponse>> {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000/api";
  const response = await fetch(`${backendUrl}/health`, { cache: "no-store" });
  return response.json();
}

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
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* Status Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <StatusCard
            title="API Status"
            value={error ? "Error" : healthStatus.status.toUpperCase()}
            status={
              error
                ? "error"
                : healthStatus.status === "ok"
                  ? "success"
                  : "warning"
            }
            error={error}
          />

          <StatusCard
            title="Database"
            value={
              healthStatus.database === "connected"
                ? "Connected"
                : "Disconnected"
            }
            status={
              healthStatus.database === "connected" ? "success" : "error"
            }
          />

          <StatusCard
            title="Current Phase"
            value="Phase 2"
            description="Market Module"
            status="neutral"
          />
        </div>

        {/* Market Dashboard */}
        <section className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">Market Overview</h2>
          <MarketDashboard />
        </section>

        {/* Module Cards */}
        <section className="mt-8">
          <h2 className="mb-4 text-lg font-semibold">Modules</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <ModuleCard
              title="Market Module"
              description="マーケット状態の判定・可視化"
              status="active"
            />

            <ModuleCard
              title="Screener Module"
              description="CAN-SLIM条件スクリーニング"
              status="coming-soon"
            />

            <ModuleCard
              title="Portfolio Module"
              description="ウォッチリスト・ペーパートレード"
              status="coming-soon"
            />
          </div>
        </section>
      </main>
    </div>
  );
}

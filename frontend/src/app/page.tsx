import { getHealth } from "@/lib/api";
import { Header } from "@/components/layout/Header";
import { StatusCard } from "@/components/ui/StatusCard";
import { ModuleCard } from "@/components/ui/ModuleCard";

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

        {/* Module Cards */}
        <h2 className="mt-8 text-lg font-semibold">Modules</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
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
      </main>
    </div>
  );
}

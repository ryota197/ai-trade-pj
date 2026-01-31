import { Header } from "@/components/layout/Header";
import { MarketDashboard } from "./_components/MarketDashboard";
import { TopStocksCard } from "./_components/TopStocksCard";
import { QuickActions } from "./_components/QuickActions";

/**
 * ダッシュボード
 *
 * - Market Overview: マーケット状態（VIX、S&P500、RSI等）
 * - Top CAN-SLIM Stocks: スコア上位銘柄
 * - Quick Actions: 主要機能へのナビゲーション
 */
export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-8 space-y-8">
        {/* Market Overview */}
        <section>
          <h2 className="mb-4 text-lg font-semibold">Market Overview</h2>
          <MarketDashboard />
        </section>

        {/* Top Stocks */}
        <section>
          <TopStocksCard />
        </section>

        {/* Quick Actions */}
        <section>
          <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
          <QuickActions />
        </section>
      </main>
    </div>
  );
}

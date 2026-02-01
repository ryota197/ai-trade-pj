"use client";

import { Button } from "@/components/ui/button";

import { useMarketStatus } from "../_hooks/useMarketStatus";
import { MarketStatus } from "./MarketStatus";
import { IndicatorCard } from "./IndicatorCard";

/**
 * マーケットダッシュボード
 *
 * マーケット状態と各種指標を表示するメインコンポーネント
 */
export function MarketDashboard() {
  const { data, isLoading, error, refetch } = useMarketStatus();

  if (isLoading && !data) {
    return (
      <div className="space-y-4">
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
        <h3 className="font-semibold text-destructive">Error</h3>
        <p className="mt-1 text-sm text-muted-foreground">{error}</p>
        <Button variant="outline" size="sm" className="mt-4" onClick={refetch}>
          Retry
        </Button>
      </div>
    );
  }

  if (!data) return null;

  const { indicators } = data;

  return (
    <div className="space-y-6">
      {/* Market Status */}
      <MarketStatus
        condition={data.condition}
        conditionLabel={data.condition_label}
        confidence={data.confidence}
        score={data.score}
        recommendation={data.recommendation}
        analyzedAt={data.analyzed_at}
      />

      {/* Indicators */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold">Indicators</h3>
          <Button
            variant="outline"
            size="sm"
            onClick={refetch}
            disabled={isLoading}
          >
            {isLoading ? "Loading..." : "Refresh"}
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <IndicatorCard
            title="VIX"
            value={indicators.vix}
            signal={indicators.vix_signal}
            description="Fear Index"
            indicatorId="vix"
          />

          <IndicatorCard
            title="S&P 500 RSI"
            value={indicators.sp500_rsi}
            signal={indicators.sp500_rsi_signal}
            description="14-day RSI"
            indicatorId="rsi"
          />

          <IndicatorCard
            title="S&P 500 Price"
            value={indicators.sp500_price}
            signal={indicators.sp500_above_ma200 ? "bullish" : "bearish"}
            format="currency"
            description={`200MA: ${indicators.sp500_ma200.toLocaleString()}`}
            indicatorId="ma200"
          />

          <IndicatorCard
            title="Put/Call Ratio"
            value={indicators.put_call_ratio}
            signal={indicators.put_call_signal}
            description="CBOE Equity P/C"
            indicatorId="put_call_ratio"
          />
        </div>
      </div>
    </div>
  );
}

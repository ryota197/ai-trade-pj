"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Performance } from "@/types/portfolio";

interface PerformanceSummaryProps {
  data: Performance | null;
  isLoading?: boolean;
}

/**
 * パフォーマンスサマリーコンポーネント
 */
export function PerformanceSummary({
  data,
  isLoading = false,
}: PerformanceSummaryProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-16 bg-muted rounded" />
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No performance data available. Start trading to see your stats.
          </p>
        </CardContent>
      </Card>
    );
  }

  const metrics = [
    {
      label: "Total Trades",
      value: data.total_trades.toString(),
      color: "text-foreground",
    },
    {
      label: "Win Rate",
      value: `${data.win_rate.toFixed(1)}%`,
      color: data.win_rate >= 50 ? "text-green-500" : "text-red-500",
    },
    {
      label: "Total P/L",
      value: `$${data.total_profit_loss.toFixed(2)}`,
      color: data.total_profit_loss >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      label: "Avg Return",
      value: `${data.average_return_percent.toFixed(2)}%`,
      color:
        data.average_return_percent >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      label: "Profit Factor",
      value: data.profit_factor?.toFixed(2) ?? "N/A",
      color:
        data.profit_factor && data.profit_factor >= 1
          ? "text-green-500"
          : "text-red-500",
    },
    {
      label: "Expectancy",
      value: `$${data.expectancy.toFixed(2)}`,
      color: data.expectancy >= 0 ? "text-green-500" : "text-red-500",
    },
    {
      label: "Max Drawdown",
      value: `${data.max_drawdown_percent.toFixed(1)}%`,
      color: "text-orange-500",
    },
    {
      label: "Avg Holding",
      value: `${data.average_holding_days.toFixed(1)} days`,
      color: "text-foreground",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Performance</span>
          {data.is_profitable ? (
            <span className="text-sm font-normal text-green-500">
              Profitable
            </span>
          ) : (
            <span className="text-sm font-normal text-red-500">
              Not Profitable
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="p-4 bg-muted/50 rounded-lg text-center"
            >
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className={`text-xl font-bold ${metric.color}`}>
                {metric.value}
              </p>
            </div>
          ))}
        </div>

        {/* 勝敗バー */}
        <div className="mt-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-green-500">
              Wins: {data.winning_trades}
            </span>
            <span className="text-red-500">Losses: {data.losing_trades}</span>
          </div>
          <div className="h-3 bg-muted rounded-full overflow-hidden flex">
            {data.total_trades > 0 && (
              <>
                <div
                  className="bg-green-500 h-full"
                  style={{
                    width: `${(data.winning_trades / data.total_trades) * 100}%`,
                  }}
                />
                <div
                  className="bg-red-500 h-full"
                  style={{
                    width: `${(data.losing_trades / data.total_trades) * 100}%`,
                  }}
                />
              </>
            )}
          </div>
        </div>

        {/* 連勝・連敗 */}
        <div className="mt-4 flex justify-center gap-8 text-sm text-muted-foreground">
          <span>
            Max Consecutive Wins:{" "}
            <span className="text-green-500 font-medium">
              {data.max_consecutive_wins}
            </span>
          </span>
          <span>
            Max Consecutive Losses:{" "}
            <span className="text-red-500 font-medium">
              {data.max_consecutive_losses}
            </span>
          </span>
        </div>

        {!data.has_sufficient_trades && (
          <p className="mt-4 text-center text-sm text-muted-foreground">
            Need at least 30 trades for statistically significant results.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

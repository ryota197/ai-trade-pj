"use client";

import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useChartData, type ChartPeriod, type ChartBar } from "../_hooks/useChartData";

interface PriceChartProps {
  symbol: string;
  height?: number;
}

const PERIOD_OPTIONS: { value: ChartPeriod; label: string }[] = [
  { value: "1mo", label: "1M" },
  { value: "3mo", label: "3M" },
  { value: "6mo", label: "6M" },
  { value: "1y", label: "1Y" },
];

/**
 * 価格チャートコンポーネント
 */
export function PriceChart({ symbol, height = 300 }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof import("lightweight-charts").createChart> | null>(null);
  const { data, isLoading, error, period, setPeriod } = useChartData(symbol);

  // チャート描画
  useEffect(() => {
    if (!data?.data || !chartContainerRef.current) return;

    const initChart = async () => {
      const { createChart, ColorType, AreaSeries } = await import("lightweight-charts");

      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }

      const container = chartContainerRef.current;
      if (!container) return;

      const firstClose = data.data[0]?.close ?? 0;
      const lastClose = data.data[data.data.length - 1]?.close ?? 0;
      const isUptrend = lastClose >= firstClose;

      const lineColor = isUptrend ? "#22c55e" : "#ef4444";
      const topColor = isUptrend ? "rgba(34, 197, 94, 0.4)" : "rgba(239, 68, 68, 0.4)";
      const bottomColor = isUptrend ? "rgba(34, 197, 94, 0.0)" : "rgba(239, 68, 68, 0.0)";

      const chart = createChart(container, {
        width: container.clientWidth,
        height: height,
        layout: {
          background: { type: ColorType.Solid, color: "transparent" },
          textColor: "#9ca3af",
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { color: "#374151", style: 1 },
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: { top: 0.1, bottom: 0.1 },
        },
        timeScale: {
          borderVisible: false,
          timeVisible: false,
        },
        crosshair: {
          vertLine: { labelVisible: false },
          horzLine: { labelVisible: true },
        },
      });

      const areaSeries = chart.addSeries(AreaSeries, {
        lineColor: lineColor,
        topColor: topColor,
        bottomColor: bottomColor,
        lineWidth: 2,
      });

      const chartData = data.data.map((bar: ChartBar) => ({
        time: bar.time,
        value: bar.close,
      }));

      areaSeries.setData(chartData);
      chart.timeScale().fitContent();
      chartRef.current = chart;

      const handleResize = () => {
        if (chartRef.current && container) {
          chartRef.current.applyOptions({ width: container.clientWidth });
        }
      };

      window.addEventListener("resize", handleResize);

      return () => {
        window.removeEventListener("resize", handleResize);
      };
    };

    initChart();

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, height]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">価格チャート</CardTitle>
          <div className="flex gap-1">
            {PERIOD_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => setPeriod(option.value)}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  period === option.value
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div
          className="rounded-lg overflow-hidden bg-muted/30"
          style={{ height: `${height}px` }}
        >
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-full text-sm text-red-500">
              {error}
            </div>
          ) : (
            <div ref={chartContainerRef} className="w-full h-full" />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

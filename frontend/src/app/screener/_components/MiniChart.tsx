"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import type { ChartBar, ChartPeriod } from "../_hooks/useChartData";
import { useChartData } from "../_hooks/useChartData";

interface MiniChartProps {
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
 * ミニチャートコンポーネント
 */
export function MiniChart({ symbol, height = 200 }: MiniChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<ReturnType<typeof import("lightweight-charts").createChart> | null>(null);
  const [period, setPeriod] = useState<ChartPeriod>("3mo");
  const { data, isLoading, error, fetchChartData, clear } = useChartData();

  // データ取得
  useEffect(() => {
    fetchChartData(symbol, period);
    return () => clear();
  }, [symbol, period, fetchChartData, clear]);

  // チャート描画
  useEffect(() => {
    if (!data?.data || !chartContainerRef.current) return;

    const initChart = async () => {
      // lightweight-chartsを動的インポート（SSR対策）
      const { createChart, ColorType, AreaSeries } = await import("lightweight-charts");

      // 既存のチャートを破棄
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }

      const container = chartContainerRef.current;
      if (!container) return;

      // トレンド判定（開始時と終了時の価格比較）
      const firstClose = data.data[0]?.close ?? 0;
      const lastClose = data.data[data.data.length - 1]?.close ?? 0;
      const isUptrend = lastClose >= firstClose;

      // カラー設定
      const lineColor = isUptrend ? "#22c55e" : "#ef4444";
      const topColor = isUptrend ? "rgba(34, 197, 94, 0.4)" : "rgba(239, 68, 68, 0.4)";
      const bottomColor = isUptrend ? "rgba(34, 197, 94, 0.0)" : "rgba(239, 68, 68, 0.0)";

      // チャート作成
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
        handleScroll: false,
        handleScale: false,
      });

      // エリアシリーズ追加（v5 API）
      const areaSeries = chart.addSeries(AreaSeries, {
        lineColor: lineColor,
        topColor: topColor,
        bottomColor: bottomColor,
        lineWidth: 2,
      });

      // データ変換（lightweight-charts形式）
      const chartData = data.data.map((bar: ChartBar) => ({
        time: bar.time,
        value: bar.close,
      }));

      areaSeries.setData(chartData);

      // 全データを表示
      chart.timeScale().fitContent();

      chartRef.current = chart;

      // リサイズ対応
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
    <div className="space-y-2">
      {/* 期間選択 */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-muted-foreground">
          価格チャート
        </span>
        <div className="flex gap-1">
          {PERIOD_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setPeriod(option.value)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
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

      {/* チャートエリア */}
      <div
        className="rounded-lg overflow-hidden bg-muted/30"
        style={{ height: `${height}px` }}
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full text-sm text-red-500">
            {error}
          </div>
        ) : (
          <div ref={chartContainerRef} className="w-full h-full" />
        )}
      </div>
    </div>
  );
}

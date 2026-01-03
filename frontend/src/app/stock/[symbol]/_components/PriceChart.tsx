"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CandlestickData,
  HistogramData,
  Time,
  CandlestickSeries,
  HistogramSeries,
} from "lightweight-charts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { PriceBar } from "@/types/stock";

interface PriceChartProps {
  data: PriceBar[];
  symbol: string;
  isLoading?: boolean;
}

/**
 * 株価チャートコンポーネント
 *
 * Lightweight Chartsを使用してローソク足チャートと出来高を表示
 */
export function PriceChart({ data, symbol, isLoading = false }: PriceChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const chartRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const candlestickSeriesRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const volumeSeriesRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // チャート作成
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "rgba(156, 163, 175, 0.1)" },
        horzLines: { color: "rgba(156, 163, 175, 0.1)" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      rightPriceScale: {
        borderColor: "rgba(156, 163, 175, 0.2)",
      },
      timeScale: {
        borderColor: "rgba(156, 163, 175, 0.2)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
        vertLine: {
          color: "rgba(156, 163, 175, 0.4)",
          width: 1,
          style: 2,
        },
        horzLine: {
          color: "rgba(156, 163, 175, 0.4)",
          width: 1,
          style: 2,
        },
      },
    });

    chartRef.current = chart;

    // ローソク足シリーズ (v5 API)
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });
    candlestickSeriesRef.current = candlestickSeries;

    // 出来高シリーズ (v5 API)
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#3b82f6",
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: {
        top: 0.85,
        bottom: 0,
      },
    });
    volumeSeriesRef.current = volumeSeries;

    // リサイズ対応
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, []);

  // データ更新
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) {
      return;
    }

    // ローソク足データ
    const candleData: CandlestickData<Time>[] = data.map((bar) => ({
      time: bar.date as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));

    // 出来高データ（色分け）
    const volumeData: HistogramData<Time>[] = data.map((bar) => ({
      time: bar.date as Time,
      value: bar.volume,
      color: bar.close >= bar.open ? "rgba(34, 197, 94, 0.5)" : "rgba(239, 68, 68, 0.5)",
    }));

    candlestickSeriesRef.current.setData(candleData);
    volumeSeriesRef.current.setData(volumeData);

    // 最新データにフィット
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="border-b">
          <CardTitle>{symbol} - 株価チャート</CardTitle>
        </CardHeader>
        <CardContent className="py-16">
          <div className="flex flex-col items-center justify-center text-muted-foreground">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4" />
            <p>チャートを読み込み中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle>{symbol} - 株価チャート（日足）</CardTitle>
      </CardHeader>
      <CardContent className="pt-4">
        <div ref={chartContainerRef} className="w-full" />
      </CardContent>
    </Card>
  );
}

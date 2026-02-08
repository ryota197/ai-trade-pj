"use client";

import { useEffect } from "react";
import { X, TrendingUp, TrendingDown, Minus, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { StockSummary, FundamentalIndicators } from "@/types/stock";
import { useFundamentals } from "../_hooks/useFundamentals";

interface FundamentalsModalProps {
  stock: StockSummary | null;
  onClose: () => void;
}

/**
 * 値のフォーマット
 */
function formatValue(value: number | null, suffix: string = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(2)}${suffix}`;
}

/**
 * PEGの評価バッジ
 */
function getPegBadge(peg: number | null) {
  if (peg === null) return <Badge variant="outline">N/A</Badge>;
  if (peg <= 1) return <Badge variant="default">割安</Badge>;
  if (peg <= 2) return <Badge variant="secondary">適正</Badge>;
  return <Badge variant="destructive">割高</Badge>;
}

/**
 * Betaの評価表示
 */
function BetaIndicator({ beta }: { beta: number | null }) {
  if (beta === null) return <span className="text-muted-foreground">N/A</span>;

  const icon =
    beta > 1.2 ? (
      <TrendingUp className="h-4 w-4 text-orange-500" />
    ) : beta < 0.8 ? (
      <TrendingDown className="h-4 w-4 text-blue-500" />
    ) : (
      <Minus className="h-4 w-4 text-gray-500" />
    );

  const label =
    beta > 1.2 ? "高ボラティリティ" : beta < 0.8 ? "低ボラティリティ" : "市場並み";

  return (
    <div className="flex items-center gap-2">
      {icon}
      <span className="font-mono">{beta.toFixed(2)}</span>
      <span className="text-xs text-muted-foreground">({label})</span>
    </div>
  );
}

/**
 * 指標行コンポーネント
 */
function IndicatorRow({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-border last:border-b-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-medium">{children}</span>
    </div>
  );
}

/**
 * ファンダメンタル指標モーダル
 */
export function FundamentalsModal({ stock, onClose }: FundamentalsModalProps) {
  const { data, isLoading, error, fetchFundamentals, clear } = useFundamentals();

  useEffect(() => {
    if (stock) {
      fetchFundamentals(stock.symbol);
    }
    return () => clear();
  }, [stock, fetchFundamentals, clear]);

  // ESCキーで閉じる
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleEsc);
    return () => window.removeEventListener("keydown", handleEsc);
  }, [onClose]);

  if (!stock) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* オーバーレイ */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* モーダル本体 */}
      <Card className="relative z-10 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <CardHeader className="border-b">
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <span className="font-mono text-xl">{stock.symbol}</span>
                <Badge variant="outline">RS {stock.rs_rating}</Badge>
                <Badge variant="secondary">Score {stock.canslim_score}</Badge>
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">{stock.name}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pt-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">読み込み中...</span>
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-500">
              <p>エラーが発生しました</p>
              <p className="text-sm">{error}</p>
            </div>
          ) : data ? (
            <div className="space-y-6">
              {/* バリュエーション */}
              <div>
                <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
                  バリュエーション
                </h3>
                <div className="bg-muted/30 rounded-lg p-3">
                  <IndicatorRow label="Forward PER">
                    <span className="font-mono">{formatValue(data.forward_pe)}</span>
                  </IndicatorRow>
                  <IndicatorRow label="PEG Ratio">
                    <div className="flex items-center gap-2">
                      <span className="font-mono">{formatValue(data.peg_ratio)}</span>
                      {getPegBadge(data.peg_ratio)}
                    </div>
                  </IndicatorRow>
                </div>
              </div>

              {/* 収益性 */}
              <div>
                <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
                  収益性
                </h3>
                <div className="bg-muted/30 rounded-lg p-3">
                  <IndicatorRow label="ROE">
                    <span className="font-mono">{formatValue(data.roe, "%")}</span>
                  </IndicatorRow>
                  <IndicatorRow label="営業利益率">
                    <span className="font-mono">
                      {formatValue(data.operating_margin, "%")}
                    </span>
                  </IndicatorRow>
                  <IndicatorRow label="売上成長率">
                    <span
                      className={`font-mono ${
                        data.revenue_growth !== null && data.revenue_growth > 0
                          ? "text-green-600"
                          : data.revenue_growth !== null && data.revenue_growth < 0
                          ? "text-red-600"
                          : ""
                      }`}
                    >
                      {data.revenue_growth !== null && data.revenue_growth > 0 && "+"}
                      {formatValue(data.revenue_growth, "%")}
                    </span>
                  </IndicatorRow>
                </div>
              </div>

              {/* リスク */}
              <div>
                <h3 className="text-sm font-semibold text-muted-foreground mb-2 uppercase tracking-wider">
                  リスク
                </h3>
                <div className="bg-muted/30 rounded-lg p-3">
                  <IndicatorRow label="Beta">
                    <BetaIndicator beta={data.beta} />
                  </IndicatorRow>
                </div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

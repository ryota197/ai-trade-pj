"use client";

import { TrendingUp, TrendingDown, Minus, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useFundamentals } from "../_hooks/useFundamentals";

interface FundamentalsCardProps {
  symbol: string;
}

function formatValue(value: number | null, suffix: string = ""): string {
  if (value === null || value === undefined) return "N/A";
  return `${value.toFixed(2)}${suffix}`;
}

function getPegBadge(peg: number | null) {
  if (peg === null) return <Badge variant="outline">N/A</Badge>;
  if (peg <= 1) return <Badge variant="default">割安</Badge>;
  if (peg <= 2) return <Badge variant="secondary">適正</Badge>;
  return <Badge variant="destructive">割高</Badge>;
}

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
 * ファンダメンタル指標カード
 */
export function FundamentalsCard({ symbol }: FundamentalsCardProps) {
  const { data, isLoading, error } = useFundamentals(symbol);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">ファンダメンタル指標</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">読み込み中...</span>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-red-500">
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
  );
}

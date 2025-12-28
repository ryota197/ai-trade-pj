"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart3,
  Target,
  Building2,
} from "lucide-react";
import type { QuoteData } from "../_hooks/useStockData";
import type { FinancialsResponse } from "@/types/stock";

interface FundamentalsCardProps {
  quote: QuoteData;
  financials: FinancialsResponse | null;
}

interface MetricItemProps {
  label: string;
  value: string | number | null;
  icon: React.ReactNode;
  suffix?: string;
  highlight?: "positive" | "negative" | "neutral";
}

function MetricItem({ label, value, icon, suffix = "", highlight = "neutral" }: MetricItemProps) {
  const colorClass =
    highlight === "positive"
      ? "text-green-600"
      : highlight === "negative"
      ? "text-red-600"
      : "text-foreground";

  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-0">
      <div className="flex items-center gap-2 text-muted-foreground">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <span className={`font-mono font-medium ${colorClass}`}>
        {value !== null && value !== undefined ? `${value}${suffix}` : "-"}
      </span>
    </div>
  );
}

/**
 * 財務指標カード
 *
 * 株価情報と財務指標を表示
 */
export function FundamentalsCard({ quote, financials }: FundamentalsCardProps) {
  const formatMarketCap = (value: number | null): string => {
    if (!value) return "-";
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  };

  const formatPercent = (value: number | null): string => {
    if (value === null || value === undefined) return "-";
    const sign = value >= 0 ? "+" : "";
    return `${sign}${value.toFixed(2)}%`;
  };

  const formatVolume = (value: number): string => {
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
    return value.toLocaleString();
  };

  const distanceFromHigh = quote.week_52_high
    ? ((quote.week_52_high - quote.price) / quote.week_52_high) * 100
    : null;

  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle>財務指標</CardTitle>
          <div className="flex items-center gap-2">
            {quote.change_percent >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
            <Badge
              variant={quote.change_percent >= 0 ? "default" : "destructive"}
            >
              {quote.change_percent >= 0 ? "+" : ""}
              {quote.change_percent.toFixed(2)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        {/* 株価セクション */}
        <div className="mb-6">
          <div className="text-3xl font-bold font-mono">
            ${quote.price.toLocaleString(undefined, {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}
          </div>
          <div
            className={`text-sm font-mono ${
              quote.change >= 0 ? "text-green-600" : "text-red-600"
            }`}
          >
            {quote.change >= 0 ? "+" : ""}
            {quote.change.toFixed(2)} ({quote.change_percent >= 0 ? "+" : ""}
            {quote.change_percent.toFixed(2)}%)
          </div>
        </div>

        {/* 基本指標 */}
        <div className="space-y-1">
          <h4 className="text-sm font-medium text-muted-foreground mb-2">基本情報</h4>
          <MetricItem
            label="時価総額"
            value={formatMarketCap(quote.market_cap)}
            icon={<Building2 className="h-4 w-4" />}
          />
          <MetricItem
            label="PER"
            value={quote.pe_ratio?.toFixed(2) ?? null}
            icon={<BarChart3 className="h-4 w-4" />}
            suffix="x"
          />
          <MetricItem
            label="出来高"
            value={formatVolume(quote.volume)}
            icon={<BarChart3 className="h-4 w-4" />}
          />
        </div>

        {/* 52週高値/安値 */}
        <div className="mt-4 space-y-1">
          <h4 className="text-sm font-medium text-muted-foreground mb-2">52週レンジ</h4>
          <MetricItem
            label="52週高値"
            value={`$${quote.week_52_high.toFixed(2)}`}
            icon={<Target className="h-4 w-4" />}
          />
          <MetricItem
            label="52週安値"
            value={`$${quote.week_52_low.toFixed(2)}`}
            icon={<Target className="h-4 w-4" />}
          />
          <MetricItem
            label="高値からの乖離"
            value={distanceFromHigh !== null ? distanceFromHigh.toFixed(2) : null}
            icon={<TrendingDown className="h-4 w-4" />}
            suffix="%"
            highlight={
              distanceFromHigh !== null
                ? distanceFromHigh <= 15
                  ? "positive"
                  : "negative"
                : "neutral"
            }
          />
        </div>

        {/* 財務指標 */}
        {financials && (
          <div className="mt-4 space-y-1">
            <h4 className="text-sm font-medium text-muted-foreground mb-2">成長指標</h4>
            <MetricItem
              label="四半期EPS成長率"
              value={formatPercent(financials.eps_growth_quarterly)}
              icon={<DollarSign className="h-4 w-4" />}
              highlight={
                financials.eps_growth_quarterly !== null
                  ? financials.eps_growth_quarterly >= 25
                    ? "positive"
                    : financials.eps_growth_quarterly < 0
                    ? "negative"
                    : "neutral"
                  : "neutral"
              }
            />
            <MetricItem
              label="年間EPS成長率"
              value={formatPercent(financials.eps_growth_annual)}
              icon={<DollarSign className="h-4 w-4" />}
              highlight={
                financials.eps_growth_annual !== null
                  ? financials.eps_growth_annual >= 25
                    ? "positive"
                    : financials.eps_growth_annual < 0
                    ? "negative"
                    : "neutral"
                  : "neutral"
              }
            />
            <MetricItem
              label="売上成長率"
              value={formatPercent(financials.revenue_growth)}
              icon={<TrendingUp className="h-4 w-4" />}
              highlight={
                financials.revenue_growth !== null
                  ? financials.revenue_growth >= 20
                    ? "positive"
                    : financials.revenue_growth < 0
                    ? "negative"
                    : "neutral"
                  : "neutral"
              }
            />
            <MetricItem
              label="利益率"
              value={formatPercent(financials.profit_margin)}
              icon={<BarChart3 className="h-4 w-4" />}
            />
            <MetricItem
              label="ROE"
              value={formatPercent(financials.roe)}
              icon={<BarChart3 className="h-4 w-4" />}
            />
            <MetricItem
              label="機関投資家保有率"
              value={formatPercent(financials.institutional_ownership)}
              icon={<Building2 className="h-4 w-4" />}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

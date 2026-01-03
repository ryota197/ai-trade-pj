"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { ScreenerFilter } from "@/types/stock";
import { DEFAULT_SCREENER_FILTER } from "@/types/stock";
import { RotateCcw, SlidersHorizontal } from "lucide-react";

interface FilterPanelProps {
  filter: ScreenerFilter;
  onFilterChange: (filter: Partial<ScreenerFilter>) => void;
  onReset: () => void;
  isLoading?: boolean;
}

interface FilterInputProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
}

function FilterInput({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  suffix = "",
}: FilterInputProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-foreground">{label}</label>
        <span className="text-sm font-mono text-muted-foreground">
          {value}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
      />
    </div>
  );
}

/**
 * スクリーニングフィルターパネル
 */
export function FilterPanel({
  filter,
  onFilterChange,
  onReset,
  isLoading = false,
}: FilterPanelProps) {
  const isDefault =
    filter.min_rs_rating === DEFAULT_SCREENER_FILTER.min_rs_rating &&
    filter.min_eps_growth_quarterly === DEFAULT_SCREENER_FILTER.min_eps_growth_quarterly &&
    filter.min_eps_growth_annual === DEFAULT_SCREENER_FILTER.min_eps_growth_annual &&
    filter.max_distance_from_52w_high === DEFAULT_SCREENER_FILTER.max_distance_from_52w_high &&
    filter.min_volume_ratio === DEFAULT_SCREENER_FILTER.min_volume_ratio &&
    filter.min_canslim_score === DEFAULT_SCREENER_FILTER.min_canslim_score;

  return (
    <Card>
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="h-5 w-5 text-muted-foreground" />
            <CardTitle>フィルター</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={isDefault || isLoading}
            className="gap-1"
          >
            <RotateCcw className="h-4 w-4" />
            リセット
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        {/* L - Leader (RS Rating) */}
        <FilterInput
          label="L - RS Rating"
          value={filter.min_rs_rating}
          onChange={(value) => onFilterChange({ min_rs_rating: value })}
          min={1}
          max={99}
          suffix=""
        />

        {/* CAN-SLIM Total Score */}
        <FilterInput
          label="CAN-SLIM スコア"
          value={filter.min_canslim_score}
          onChange={(value) => onFilterChange({ min_canslim_score: value })}
          min={0}
          max={100}
          suffix=""
        />

        {/* C - Current Quarterly Earnings */}
        <FilterInput
          label="C - 四半期EPS成長率"
          value={filter.min_eps_growth_quarterly}
          onChange={(value) => onFilterChange({ min_eps_growth_quarterly: value })}
          min={0}
          max={100}
          step={5}
          suffix="%"
        />

        {/* A - Annual Earnings */}
        <FilterInput
          label="A - 年間EPS成長率"
          value={filter.min_eps_growth_annual}
          onChange={(value) => onFilterChange({ min_eps_growth_annual: value })}
          min={0}
          max={100}
          step={5}
          suffix="%"
        />

        {/* N - New High */}
        <FilterInput
          label="N - 52週高値乖離率"
          value={filter.max_distance_from_52w_high}
          onChange={(value) => onFilterChange({ max_distance_from_52w_high: value })}
          min={0}
          max={50}
          step={5}
          suffix="%"
        />

        {/* S - Supply and Demand */}
        <FilterInput
          label="S - 出来高倍率"
          value={filter.min_volume_ratio}
          onChange={(value) => onFilterChange({ min_volume_ratio: value })}
          min={0}
          max={5}
          step={0.1}
          suffix="x"
        />

        {/* フィルター説明 */}
        <div className="pt-4 border-t text-xs text-muted-foreground space-y-1">
          <p>
            <strong>C</strong> - Current Quarterly Earnings: 四半期EPS成長率
          </p>
          <p>
            <strong>A</strong> - Annual Earnings: 年間EPS成長率
          </p>
          <p>
            <strong>N</strong> - New High: 52週高値からの乖離
          </p>
          <p>
            <strong>S</strong> - Supply and Demand: 出来高倍率
          </p>
          <p>
            <strong>L</strong> - Leader: RS Rating（相対力指数）
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

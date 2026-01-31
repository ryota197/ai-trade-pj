"use client";

import { StockDetail } from "@/types/stock";

interface PriceInfoProps {
  stock: StockDetail;
}

function InfoRow({
  label,
  value,
  suffix = "",
}: {
  label: string;
  value: string | number | null;
  suffix?: string;
}) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-600">{label}</span>
      <span className="font-medium">
        {value !== null ? `${value}${suffix}` : "N/A"}
      </span>
    </div>
  );
}

function formatNumber(num: number | null): string {
  if (num === null) return "N/A";
  if (num >= 1_000_000_000_000) {
    return `$${(num / 1_000_000_000_000).toFixed(2)}T`;
  }
  if (num >= 1_000_000_000) {
    return `$${(num / 1_000_000_000).toFixed(2)}B`;
  }
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2)}M`;
  }
  return num.toLocaleString();
}

function formatVolume(num: number | null): string {
  if (num === null) return "N/A";
  if (num >= 1_000_000) {
    return `${(num / 1_000_000).toFixed(2)}M`;
  }
  if (num >= 1_000) {
    return `${(num / 1_000).toFixed(1)}K`;
  }
  return num.toLocaleString();
}

export function PriceInfo({ stock }: PriceInfoProps) {
  const distanceFrom52High =
    stock.week_52_high > 0
      ? (((stock.week_52_high - stock.price) / stock.week_52_high) * 100).toFixed(1)
      : null;

  const volumeRatio =
    stock.avg_volume > 0
      ? (stock.volume / stock.avg_volume).toFixed(2)
      : null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* 価格情報 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">価格情報</h2>
        <div className="space-y-1">
          <InfoRow
            label="52週高値"
            value={stock.week_52_high ? `$${stock.week_52_high.toFixed(2)}` : null}
          />
          <InfoRow
            label="52週安値"
            value={stock.week_52_low ? `$${stock.week_52_low.toFixed(2)}` : null}
          />
          <InfoRow
            label="高値からの距離"
            value={distanceFrom52High}
            suffix="%"
          />
          <InfoRow label="出来高" value={formatVolume(stock.volume)} />
          <InfoRow label="平均出来高" value={formatVolume(stock.avg_volume)} />
          <InfoRow label="出来高比率" value={volumeRatio} suffix="x" />
          <InfoRow label="時価総額" value={formatNumber(stock.market_cap)} />
          <InfoRow
            label="PER"
            value={stock.pe_ratio?.toFixed(2) ?? null}
          />
        </div>
      </div>

      {/* ファンダメンタル */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold mb-4">ファンダメンタル</h2>
        <div className="space-y-1">
          <InfoRow
            label="RS Rating"
            value={stock.rs_rating}
          />
          <InfoRow
            label="EPS成長率（四半期）"
            value={stock.eps_growth_quarterly?.toFixed(1) ?? null}
            suffix="%"
          />
          <InfoRow
            label="EPS成長率（年間）"
            value={stock.eps_growth_annual?.toFixed(1) ?? null}
            suffix="%"
          />
          <InfoRow
            label="機関投資家保有率"
            value={stock.institutional_ownership?.toFixed(1) ?? null}
            suffix="%"
          />
        </div>
      </div>
    </div>
  );
}

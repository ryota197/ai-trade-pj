"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { MarketCondition } from "@/types/market";

interface MarketStatusProps {
  condition: MarketCondition;
  conditionLabel: string;
  confidence: number;
  score: number;
  recommendation: string;
  analyzedAt: string;
}

const conditionStyles: Record<
  MarketCondition,
  { badge: "default" | "destructive" | "secondary"; bg: string }
> = {
  risk_on: { badge: "default", bg: "bg-green-500/10 border-green-500/20" },
  risk_off: { badge: "destructive", bg: "bg-red-500/10 border-red-500/20" },
  neutral: { badge: "secondary", bg: "bg-yellow-500/10 border-yellow-500/20" },
};

/**
 * マーケット状態表示コンポーネント
 */
export function MarketStatus({
  condition,
  conditionLabel,
  confidence,
  score,
  recommendation,
  analyzedAt,
}: MarketStatusProps) {
  const style = conditionStyles[condition];

  return (
    <Card className={cn("border-2", style.bg)}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Market Status</CardTitle>
          <Badge variant={style.badge} className="text-sm">
            {conditionLabel}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Score</p>
            <p className="text-2xl font-bold">
              {score > 0 ? `+${score}` : score}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Confidence</p>
            <p className="text-2xl font-bold">{(confidence * 100).toFixed(0)}%</p>
          </div>
        </div>

        <div>
          <p className="text-sm text-muted-foreground">Recommendation</p>
          <p className="mt-1 text-sm">{recommendation}</p>
        </div>

        <p className="text-xs text-muted-foreground">
          Last updated: {new Date(analyzedAt).toLocaleString("ja-JP")}
        </p>
      </CardContent>
    </Card>
  );
}

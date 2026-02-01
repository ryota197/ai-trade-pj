import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SignalType } from "@/types/market";
import type { IndicatorId } from "@/lib/indicator-guide";
import { IndicatorInfoPopover } from "./IndicatorInfoPopover";

interface IndicatorCardProps {
  title: string;
  value: string | number;
  signal: SignalType;
  description?: string;
  format?: "number" | "percent" | "currency";
  /** 指標ID（指定するとヘルプアイコンを表示） */
  indicatorId?: IndicatorId;
}

const signalStyles: Record<
  SignalType,
  { variant: "default" | "destructive" | "secondary"; label: string }
> = {
  bullish: { variant: "default", label: "Bullish" },
  bearish: { variant: "destructive", label: "Bearish" },
  neutral: { variant: "secondary", label: "Neutral" },
};

/**
 * 指標表示カード
 */
export function IndicatorCard({
  title,
  value,
  signal,
  description,
  format = "number",
  indicatorId,
}: IndicatorCardProps) {
  const style = signalStyles[signal];

  const formatValue = (val: string | number): string => {
    if (typeof val === "string") return val;

    switch (format) {
      case "percent":
        return `${val.toFixed(2)}%`;
      case "currency":
        return val.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
      default:
        return val.toLocaleString("en-US", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });
    }
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {title}
            </CardTitle>
            {indicatorId && <IndicatorInfoPopover indicatorId={indicatorId} />}
          </div>
          <Badge variant={style.variant} className="text-xs">
            {style.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{formatValue(value)}</p>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

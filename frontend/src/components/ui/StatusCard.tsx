import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type StatusType = "success" | "error" | "warning" | "neutral";

interface StatusCardProps {
  title: string;
  value: string;
  description?: string;
  status?: StatusType;
  error?: string | null;
}

const statusColors: Record<StatusType, string> = {
  success: "bg-green-500",
  error: "bg-red-500",
  warning: "bg-yellow-500",
  neutral: "bg-zinc-400",
};

/**
 * ステータス表示カード
 *
 * API接続状態やDB接続状態などのステータスを表示するカード
 */
export function StatusCard({
  title,
  value,
  description,
  status = "neutral",
  error,
}: StatusCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <span
            className={cn("h-3 w-3 rounded-full", statusColors[status])}
            aria-hidden="true"
          />
          <span className="text-lg font-semibold">{value}</span>
        </div>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
        {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
      </CardContent>
    </Card>
  );
}

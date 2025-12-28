/**
 * ProgressBar Component
 * 進捗バー表示コンポーネント
 */

interface ProgressBarProps {
  /** 進捗率 (0-100) */
  percentage: number;
  /** 処理済み数 */
  processed: number;
  /** 合計数 */
  total: number;
  /** 成功数 */
  succeeded: number;
  /** 失敗数 */
  failed: number;
}

export function ProgressBar({
  percentage,
  processed,
  total,
  succeeded,
  failed,
}: ProgressBarProps) {
  return (
    <div className="space-y-3">
      {/* プログレスバー */}
      <div className="relative h-4 bg-muted rounded-full overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 bg-primary transition-all duration-300 ease-out"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
        {/* 失敗分を赤で表示 */}
        {failed > 0 && (
          <div
            className="absolute inset-y-0 bg-destructive transition-all duration-300 ease-out"
            style={{
              left: `${((succeeded) / total) * 100}%`,
              width: `${(failed / total) * 100}%`,
            }}
          />
        )}
      </div>

      {/* 進捗詳細 */}
      <div className="flex items-center justify-between text-sm">
        <div className="text-muted-foreground">
          {processed} / {total} 銘柄処理済み
        </div>
        <div className="font-medium">{percentage.toFixed(1)}%</div>
      </div>

      {/* 成功/失敗カウント */}
      <div className="flex gap-4 text-sm">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span className="text-muted-foreground">成功:</span>
          <span className="font-medium text-green-600">{succeeded}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-muted-foreground">失敗:</span>
          <span className="font-medium text-red-600">{failed}</span>
        </div>
      </div>
    </div>
  );
}

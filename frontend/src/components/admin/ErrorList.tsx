/**
 * ErrorList Component
 * エラー一覧表示コンポーネント
 */

import { AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface ErrorItem {
  symbol: string;
  error: string;
}

interface ErrorListProps {
  /** エラー一覧 */
  errors: ErrorItem[];
  /** 最大表示件数（デフォルト: 5） */
  maxVisible?: number;
}

export function ErrorList({ errors, maxVisible = 5 }: ErrorListProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (errors.length === 0) {
    return null;
  }

  const visibleErrors = isExpanded ? errors : errors.slice(0, maxVisible);
  const hasMore = errors.length > maxVisible;

  return (
    <div className="mt-4 p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
      <div className="flex items-center gap-2 mb-3">
        <AlertCircle className="h-4 w-4 text-destructive" />
        <span className="font-medium text-destructive">
          エラー ({errors.length}件)
        </span>
      </div>

      <div className="space-y-2">
        {visibleErrors.map((err, index) => (
          <div
            key={`${err.symbol}-${index}`}
            className="flex items-start gap-2 text-sm"
          >
            <span className="font-mono font-medium text-foreground min-w-[60px]">
              {err.symbol}
            </span>
            <span className="text-muted-foreground">{err.error}</span>
          </div>
        ))}
      </div>

      {hasMore && (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="mt-3 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="h-4 w-4" />
              折りたたむ
            </>
          ) : (
            <>
              <ChevronDown className="h-4 w-4" />
              さらに {errors.length - maxVisible} 件を表示
            </>
          )}
        </button>
      )}
    </div>
  );
}

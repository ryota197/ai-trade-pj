/**
 * 管理画面用フォーマットユーティリティ
 */

/**
 * 実行時間を計算してフォーマット
 *
 * @param startedAt 開始日時
 * @param completedAt 完了日時
 * @param options オプション
 * @returns フォーマットされた実行時間
 */
export function formatDuration(
  startedAt: string | null,
  completedAt: string | null,
  options?: { short?: boolean }
): string {
  if (!startedAt || !completedAt) return "";
  const start = new Date(startedAt).getTime();
  const end = new Date(completedAt).getTime();
  const seconds = (end - start) / 1000;

  if (options?.short) {
    // 短縮形式: "12.3s", "2m 30s"
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    }
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  }

  // 通常形式: "12秒", "2分30秒"
  if (seconds < 60) {
    return `${seconds.toFixed(0)}秒`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.floor(seconds % 60);
  return `${minutes}分${remainingSeconds}秒`;
}

/**
 * 日時をフォーマット
 *
 * @param dateStr ISO 8601形式の日時文字列
 * @returns フォーマットされた日時
 */
export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleString("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

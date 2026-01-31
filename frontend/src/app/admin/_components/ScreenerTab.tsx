"use client";

import { RefreshPanel } from "../screener/_components/RefreshPanel";
import { FlowHistory } from "../screener/_components/FlowHistory";

/**
 * スクリーナータブ - スクリーニングデータ更新
 */
export function ScreenerTab() {
  return (
    <div className="space-y-6">
      {/* 更新パネル */}
      <RefreshPanel />

      {/* 実行履歴 */}
      <FlowHistory />

      {/* 注意事項 */}
      <div className="p-4 bg-muted/50 rounded-lg">
        <h3 className="font-medium mb-2">注意事項</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• 更新処理には数分〜数十分かかる場合があります</li>
          <li>
            • Yahoo Finance APIのレート制限により、一部の銘柄でエラーが発生する可能性があります
          </li>
          <li>
            • 更新中にページを閉じても、バックグラウンドで処理は継続されます
          </li>
          <li>
            • 頻繁な更新はAPIレート制限に抵触する可能性があるため、1日1回程度を推奨します
          </li>
        </ul>
      </div>
    </div>
  );
}

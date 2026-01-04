"use client";

import { Header } from "@/components/layout/Header";
import { Shield } from "lucide-react";

import { RefreshPanel } from "./_components/RefreshPanel";
import { FlowHistory } from "./_components/FlowHistory";

/**
 * 管理画面 - スクリーナーデータ更新ページ
 */
export default function AdminScreenerPage() {
  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">
                管理画面
              </h1>
              <p className="text-sm text-muted-foreground mt-1">
                スクリーニングデータの管理と更新
              </p>
            </div>
          </div>
        </div>

        {/* 更新パネル */}
        <RefreshPanel />

        {/* 実行履歴 */}
        <div className="mt-6">
          <FlowHistory />
        </div>

        {/* 注意事項 */}
        <div className="mt-8 p-4 bg-muted/50 rounded-lg">
          <h3 className="font-medium mb-2">注意事項</h3>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• 更新処理には数分〜数十分かかる場合があります</li>
            <li>• Yahoo Finance APIのレート制限により、一部の銘柄でエラーが発生する可能性があります</li>
            <li>• 更新中にページを閉じても、バックグラウンドで処理は継続されます</li>
            <li>• 頻繁な更新はAPIレート制限に抵触する可能性があるため、1日1回程度を推奨します</li>
          </ul>
        </div>
      </main>
    </div>
  );
}

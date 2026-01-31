"use client";

import { Header } from "@/components/layout/Header";
import { Shield } from "lucide-react";

import { AdminTabs } from "./_components/AdminTabs";
import { ScreenerTab } from "./_components/ScreenerTab";
import { MarketTab } from "./_components/MarketTab";

/**
 * 管理画面 - タブ式統合ページ
 */
export default function AdminPage() {
  const tabs = [
    {
      id: "screener",
      label: "スクリーナー",
      content: <ScreenerTab />,
    },
    {
      id: "market",
      label: "マーケット",
      content: <MarketTab />,
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-4xl px-4 py-8">
        {/* ページヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Shield className="h-6 w-6 text-primary" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">管理画面</h1>
              <p className="text-sm text-muted-foreground mt-1">
                データの管理と更新
              </p>
            </div>
          </div>
        </div>

        {/* タブ */}
        <AdminTabs tabs={tabs} defaultTab="screener" />
      </main>
    </div>
  );
}

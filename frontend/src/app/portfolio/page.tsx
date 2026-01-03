"use client";

import { useState } from "react";
import { Header } from "@/components/layout/Header";

import { WatchlistTable } from "./_components/WatchlistTable";
import { AddToWatchlistButton } from "./_components/AddToWatchlistButton";
import { TradeHistory } from "./_components/TradeHistory";
import { TradeForm } from "./_components/TradeForm";
import { PerformanceSummary } from "./_components/PerformanceSummary";
import { useWatchlist } from "./_hooks/useWatchlist";
import { useTrades } from "./_hooks/useTrades";
import { usePerformance } from "./_hooks/usePerformance";

type TabType = "watchlist" | "trades" | "performance";

export default function PortfolioPage() {
  const [activeTab, setActiveTab] = useState<TabType>("watchlist");

  // Hooks
  const watchlist = useWatchlist();
  const trades = useTrades();
  const performance = usePerformance();

  const tabs: { id: TabType; label: string; count?: number }[] = [
    {
      id: "watchlist",
      label: "Watchlist",
      count: watchlist.data?.watching_count,
    },
    {
      id: "trades",
      label: "Trades",
      count: trades.data?.open_count,
    },
    {
      id: "performance",
      label: "Performance",
    },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Portfolio</h1>
          <p className="text-muted-foreground mt-1">
            Manage your watchlist and paper trades
          </p>
        </div>
        {activeTab === "watchlist" && (
          <div className="mt-4 md:mt-0">
            <AddToWatchlistButton
              onAdd={async (data) => {
                await watchlist.add(data);
              }}
              isAdding={watchlist.isAdding}
            />
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b mb-6">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                activeTab === tab.id
                  ? "text-primary"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary">
                  {tab.count}
                </span>
              )}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {(watchlist.error || trades.error || performance.error) && (
        <div className="mb-6 p-4 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg">
          {watchlist.error || trades.error || performance.error}
        </div>
      )}

      {/* Tab Content */}
      {activeTab === "watchlist" && (
        <div className="space-y-6">
          <WatchlistTable
            items={watchlist.data?.items ?? []}
            isLoading={watchlist.isLoading}
            onRemove={async (symbol) => {
              await watchlist.remove(symbol);
            }}
          />
        </div>
      )}

      {activeTab === "trades" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <TradeHistory
              trades={trades.data?.trades ?? []}
              isLoading={trades.isLoading}
              onClose={async (tradeId, exitPrice) => {
                await trades.close(tradeId, { exit_price: exitPrice });
              }}
              onCancel={async (tradeId) => {
                await trades.cancel(tradeId);
              }}
            />
          </div>
          <div>
            <TradeForm
              onSubmit={async (data) => {
                await trades.open(data);
              }}
              isSubmitting={trades.isCreating}
            />
          </div>
        </div>
      )}

      {activeTab === "performance" && (
        <div className="space-y-6">
          <PerformanceSummary
            data={performance.data}
            isLoading={performance.isLoading}
          />

          {/* Quick Stats */}
          {trades.data && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-muted/50 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Total Trades</p>
                <p className="text-2xl font-bold">{trades.data.total_count}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Open Positions</p>
                <p className="text-2xl font-bold text-blue-500">
                  {trades.data.open_count}
                </p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Closed Trades</p>
                <p className="text-2xl font-bold">{trades.data.closed_count}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-lg text-center">
                <p className="text-sm text-muted-foreground">Watchlist</p>
                <p className="text-2xl font-bold">
                  {watchlist.data?.watching_count ?? 0}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
      </main>
    </div>
  );
}

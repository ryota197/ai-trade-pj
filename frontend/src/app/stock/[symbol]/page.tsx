"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { StockDetail } from "@/types/stock";
import { StockHeader } from "./_components/StockHeader";
import { CANSLIMScoreCard } from "./_components/CANSLIMScoreCard";
import { PriceInfo } from "./_components/PriceInfo";

export default function StockDetailPage() {
  const params = useParams();
  const symbol = params.symbol as string;

  const [stock, setStock] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStock() {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`/api/screener/stock/${symbol}`);

        if (!res.ok) {
          if (res.status === 404) {
            throw new Error(`銘柄 ${symbol} が見つかりませんでした`);
          }
          throw new Error("データの取得に失敗しました");
        }

        const json = await res.json();
        // ApiResponse 形式の場合は data を取り出す
        const data = json.data ?? json;
        setStock(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "エラーが発生しました");
      } finally {
        setLoading(false);
      }
    }

    if (symbol) {
      fetchStock();
    }
  }, [symbol]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 text-lg">{error}</p>
          <a
            href="/screener"
            className="mt-4 inline-block text-blue-600 hover:underline"
          >
            スクリーナーに戻る
          </a>
        </div>
      </div>
    );
  }

  if (!stock) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* ヘッダー */}
        <StockHeader stock={stock} />

        {/* メインコンテンツ */}
        <div className="mt-8 space-y-6">
          {/* CAN-SLIMスコア */}
          {stock.canslim_score && (
            <CANSLIMScoreCard score={stock.canslim_score} />
          )}

          {/* 価格情報・ファンダメンタル */}
          <PriceInfo stock={stock} />
        </div>
      </div>
    </div>
  );
}

/**
 * Chart Data API Route
 * GET /api/screener/stock/[symbol]/chart - チャートデータ取得
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { PriceHistoryResponse } from "@/types/stock";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ symbol: string }> }
) {
  const { symbol } = await params;

  if (!symbol) {
    return NextResponse.json(
      {
        success: false,
        data: null,
        error: { code: "VALIDATION_ERROR", message: "Symbol is required" },
      },
      { status: 400 }
    );
  }

  // クエリパラメータから期間を取得
  const { searchParams } = new URL(request.url);
  const period = searchParams.get("period") || "3mo";

  // 期間のバリデーション
  if (!["1mo", "3mo", "6mo", "1y"].includes(period)) {
    return NextResponse.json(
      {
        success: false,
        data: null,
        error: { code: "VALIDATION_ERROR", message: "Invalid period" },
      },
      { status: 400 }
    );
  }

  const result = await backendGet<ApiResponse<PriceHistoryResponse>>(
    `/screener/stock/${symbol.toUpperCase()}/chart?period=${period}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

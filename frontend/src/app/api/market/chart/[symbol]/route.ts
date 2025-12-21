/**
 * Stock Chart (Price History) API Route
 * GET /api/market/chart/[symbol]?period=1y&interval=1d
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, buildQueryString } from "@/lib/backend-fetch";
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

  // クエリパラメータを取得
  const searchParams = request.nextUrl.searchParams;
  const period = searchParams.get("period") || "1y";
  const interval = searchParams.get("interval") || "1d";

  const queryString = buildQueryString({ period, interval });
  const endpoint = `/data/history/${symbol.toUpperCase()}${queryString}`;

  const result = await backendGet<ApiResponse<PriceHistoryResponse>>(endpoint, {
    // チャートデータはある程度キャッシュ可能
    next: { revalidate: 60 },
  });

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

/**
 * Price History API Route
 * GET /api/data/history/[symbol] - 株価履歴取得
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

  const searchParams = request.nextUrl.searchParams;
  const queryString = buildQueryString({
    period: searchParams.get("period") || "1y",
    interval: searchParams.get("interval") || "1d",
  });

  const result = await backendGet<ApiResponse<PriceHistoryResponse>>(
    `/data/history/${symbol.toUpperCase()}${queryString}`,
    { next: { revalidate: 60 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

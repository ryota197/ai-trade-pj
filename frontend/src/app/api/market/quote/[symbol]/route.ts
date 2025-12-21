/**
 * Stock Quote API Route
 * GET /api/market/quote/[symbol]
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";

interface QuoteResponse {
  symbol: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: number | null;
  pe_ratio: number | null;
  week_52_high: number;
  week_52_low: number;
  timestamp: string;
}

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

  const result = await backendGet<ApiResponse<QuoteResponse>>(
    `/data/quote/${symbol.toUpperCase()}`,
    {
      // リアルタイム性が必要なのでキャッシュしない
      next: { revalidate: 0 },
    }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

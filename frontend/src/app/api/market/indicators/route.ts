/**
 * Market Indicators API Route
 * GET /api/market/indicators
 */

import { NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { MarketIndicatorsResponse } from "@/types/market";

export async function GET() {
  const result = await backendGet<ApiResponse<MarketIndicatorsResponse>>(
    "/market/indicators",
    {
      next: { revalidate: 30 }, // 30秒キャッシュ
    }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

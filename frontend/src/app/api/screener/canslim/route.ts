/**
 * CAN-SLIM Screener API Route
 * GET /api/screener/canslim - CAN-SLIMスクリーニング実行
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, buildQueryString } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { ScreenerResponse } from "@/types/stock";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  const queryString = buildQueryString({
    min_rs_rating: searchParams.get("min_rs_rating") || undefined,
    min_eps_growth_quarterly: searchParams.get("min_eps_growth_quarterly") || undefined,
    min_eps_growth_annual: searchParams.get("min_eps_growth_annual") || undefined,
    max_distance_from_52w_high: searchParams.get("max_distance_from_52w_high") || undefined,
    min_volume_ratio: searchParams.get("min_volume_ratio") || undefined,
    min_canslim_score: searchParams.get("min_canslim_score") || undefined,
  });

  const result = await backendGet<ApiResponse<ScreenerResponse>>(
    `/screener/canslim${queryString}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

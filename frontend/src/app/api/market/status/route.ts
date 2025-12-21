/**
 * Market Status API Route
 * GET /api/market/status
 */

import { NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { MarketStatusResponse } from "@/types/market";

export async function GET() {
  const result = await backendGet<ApiResponse<MarketStatusResponse>>(
    "/market/status",
    {
      next: { revalidate: 60 }, // 60秒キャッシュ
    }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

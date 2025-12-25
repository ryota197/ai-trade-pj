/**
 * Performance API Route
 * GET /api/performance - パフォーマンス取得
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, buildQueryString } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { Performance } from "@/types/portfolio";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  const queryString = buildQueryString({
    start_date: searchParams.get("start_date") || undefined,
    end_date: searchParams.get("end_date") || undefined,
  });

  const result = await backendGet<ApiResponse<Performance>>(
    `/portfolio/performance${queryString}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

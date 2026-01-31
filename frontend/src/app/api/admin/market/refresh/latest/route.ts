/**
 * Admin Market Refresh Latest API Route
 * GET /api/admin/market/refresh/latest - マーケット更新フロー一覧取得
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { FlowStatusResponse } from "@/types/admin";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const limit = searchParams.get("limit") || "10";

  const result = await backendGet<ApiResponse<FlowStatusResponse[]>>(
    `/admin/market/refresh/latest?limit=${limit}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

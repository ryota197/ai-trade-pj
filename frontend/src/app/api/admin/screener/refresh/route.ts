/**
 * Admin Screener Refresh API Route
 * POST /api/admin/screener/refresh - スクリーニングデータ更新開始
 */

import { NextResponse } from "next/server";
import { backendPost } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { RefreshResponse } from "@/types/admin";

export async function POST() {
  const result = await backendPost<ApiResponse<RefreshResponse>>(
    "/admin/screener/refresh",
    {}
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data, { status: 201 });
}

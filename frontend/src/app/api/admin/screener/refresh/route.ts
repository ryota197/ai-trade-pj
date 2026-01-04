/**
 * Admin Screener Refresh API Route
 * POST /api/admin/screener/refresh - スクリーニングデータ更新開始
 */

import { NextRequest, NextResponse } from "next/server";
import { backendPost } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { RefreshResponse, RefreshRequest } from "@/types/admin";

export async function POST(request: NextRequest) {
  let body: RefreshRequest;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      {
        success: false,
        data: null,
        error: { code: "VALIDATION_ERROR", message: "Invalid JSON body" },
      },
      { status: 400 }
    );
  }

  const result = await backendPost<ApiResponse<RefreshResponse>>(
    "/admin/screener/refresh",
    body
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data, { status: 201 });
}

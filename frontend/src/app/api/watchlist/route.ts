/**
 * Watchlist API Route
 * GET /api/watchlist - ウォッチリスト一覧取得
 * POST /api/watchlist - ウォッチリスト追加
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, backendPost, buildQueryString } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type {
  WatchlistResponse,
  WatchlistItem,
  AddToWatchlistRequest,
} from "@/types/portfolio";

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;

  const queryString = buildQueryString({
    status: searchParams.get("status") || undefined,
    limit: searchParams.get("limit") || undefined,
    offset: searchParams.get("offset") || undefined,
  });

  const result = await backendGet<ApiResponse<WatchlistResponse>>(
    `/portfolio/watchlist${queryString}`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

export async function POST(request: NextRequest) {
  let body: AddToWatchlistRequest;

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

  const result = await backendPost<ApiResponse<WatchlistItem>>(
    "/portfolio/watchlist",
    body
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data, { status: 201 });
}

/**
 * Watchlist Item API Route
 * PUT /api/watchlist/[symbol] - ウォッチリスト更新
 * DELETE /api/watchlist/[symbol] - ウォッチリスト削除
 */

import { NextRequest, NextResponse } from "next/server";
import { backendPut, backendDelete } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { WatchlistItem, UpdateWatchlistRequest } from "@/types/portfolio";

export async function PUT(
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

  let body: UpdateWatchlistRequest;

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

  const result = await backendPut<ApiResponse<WatchlistItem>>(
    `/portfolio/watchlist/${symbol.toUpperCase()}`,
    body
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

export async function DELETE(
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

  const result = await backendDelete<ApiResponse<{ message: string }>>(
    `/portfolio/watchlist/${symbol.toUpperCase()}`
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

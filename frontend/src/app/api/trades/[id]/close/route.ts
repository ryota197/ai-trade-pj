/**
 * Close Trade API Route
 * POST /api/trades/[id]/close - トレード決済
 */

import { NextRequest, NextResponse } from "next/server";
import { backendPost } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { Trade, CloseTradeRequest } from "@/types/portfolio";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  if (!id || isNaN(Number(id))) {
    return NextResponse.json(
      {
        success: false,
        data: null,
        error: { code: "VALIDATION_ERROR", message: "Valid trade ID is required" },
      },
      { status: 400 }
    );
  }

  let body: CloseTradeRequest;

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

  const result = await backendPost<ApiResponse<Trade>>(
    `/portfolio/trades/${id}/close`,
    body
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

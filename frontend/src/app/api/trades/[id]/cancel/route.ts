/**
 * Cancel Trade API Route
 * POST /api/trades/[id]/cancel - トレードキャンセル（別エンドポイント）
 *
 * Note: DELETEと同じ機能だが、RESTful以外のクライアント対応用
 */

import { NextRequest, NextResponse } from "next/server";
import { backendDelete } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";

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

  const result = await backendDelete<ApiResponse<{ message: string }>>(
    `/portfolio/trades/${id}`
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

/**
 * Admin Screener Refresh Flow API Route
 * GET /api/admin/screener/refresh/[flowId] - フローステータス取得
 * DELETE /api/admin/screener/refresh/[flowId] - フローキャンセル（未実装）
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, backendDelete } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { FlowStatusResponse } from "@/types/admin";

interface CancelFlowResponse {
  message: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ flowId: string }> }
) {
  const { flowId } = await params;

  const result = await backendGet<ApiResponse<FlowStatusResponse>>(
    `/admin/screener/refresh/${flowId}/status`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ flowId: string }> }
) {
  const { flowId } = await params;

  const result = await backendDelete<ApiResponse<CancelFlowResponse>>(
    `/admin/screener/refresh/${flowId}`
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

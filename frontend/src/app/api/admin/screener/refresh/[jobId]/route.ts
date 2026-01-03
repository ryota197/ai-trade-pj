/**
 * Admin Screener Refresh Job API Route
 * GET /api/admin/screener/refresh/[jobId] - ジョブステータス取得
 * DELETE /api/admin/screener/refresh/[jobId] - ジョブキャンセル
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet, backendDelete } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";

interface RefreshJobProgress {
  total: number;
  processed: number;
  succeeded: number;
  failed: number;
  percentage: number;
}

interface RefreshJobTiming {
  started_at: string | null;
  elapsed_seconds: number;
  estimated_remaining_seconds: number | null;
}

interface RefreshJobError {
  symbol: string;
  error: string;
}

interface RefreshJobStatusResponse {
  job_id: string;
  status: string;
  progress: RefreshJobProgress;
  timing: RefreshJobTiming;
  errors: RefreshJobError[];
}

interface CancelJobResponse {
  message: string;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  const result = await backendGet<ApiResponse<RefreshJobStatusResponse>>(
    `/admin/screener/refresh/${jobId}/status`,
    { next: { revalidate: 0 } }
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  const result = await backendDelete<ApiResponse<CancelJobResponse>>(
    `/admin/screener/refresh/${jobId}`
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

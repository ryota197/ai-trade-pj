/**
 * Financials API Route
 * GET /api/data/financials/[symbol] - 財務指標取得
 */

import { NextRequest, NextResponse } from "next/server";
import { backendGet } from "@/lib/backend-fetch";
import type { ApiResponse } from "@/types/api";
import type { FinancialsResponse } from "@/types/stock";

export async function GET(
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

  const result = await backendGet<ApiResponse<FinancialsResponse>>(
    `/data/financials/${symbol.toUpperCase()}`,
    { next: { revalidate: 300 } } // 5分キャッシュ
  );

  if (!result.ok) {
    return NextResponse.json(result.error, { status: result.status || 500 });
  }

  return NextResponse.json(result.data);
}

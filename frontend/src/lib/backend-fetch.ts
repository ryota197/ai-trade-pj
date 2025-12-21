/**
 * Backend Fetch Utility
 *
 * サーバーサイドからバックエンドAPIを呼び出すためのユーティリティ
 * Next.js Route Handlers (BFF) で使用
 */

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000/api";

/**
 * エラーレスポンスの型
 */
export interface BackendErrorResponse {
  success: false;
  data: null;
  error: {
    code: string;
    message: string;
  };
}

/**
 * fetchオプションの拡張型
 */
export interface BackendFetchOptions extends Omit<RequestInit, "next"> {
  /**
   * Next.js のキャッシュ設定
   */
  next?: {
    revalidate?: number | false;
    tags?: string[];
  };
  /**
   * タイムアウト（ミリ秒）
   */
  timeout?: number;
}

/**
 * バックエンドAPIへのリクエスト結果
 */
export type BackendResult<T> =
  | { ok: true; data: T; status: number }
  | { ok: false; error: BackendErrorResponse; status: number };

/**
 * タイムアウト付きfetch
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * バックエンドAPIを呼び出す
 *
 * @param endpoint - APIエンドポイント（例: "/market/status"）
 * @param options - fetchオプション
 * @returns 結果オブジェクト
 *
 * @example
 * ```typescript
 * const result = await backendFetch<MarketStatus>("/market/status");
 * if (result.ok) {
 *   console.log(result.data);
 * } else {
 *   console.error(result.error);
 * }
 * ```
 */
export async function backendFetch<T>(
  endpoint: string,
  options: BackendFetchOptions = {}
): Promise<BackendResult<T>> {
  const { timeout = 30000, next, ...fetchOptions } = options;

  const url = `${BACKEND_URL}${endpoint}`;

  const requestOptions: RequestInit & { next?: BackendFetchOptions["next"] } = {
    ...fetchOptions,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...fetchOptions.headers,
    },
  };

  // Next.js のキャッシュ設定を追加
  if (next) {
    requestOptions.next = next;
  }

  try {
    const response = await fetchWithTimeout(url, requestOptions, timeout);

    // レスポンスをJSONとしてパース
    let data: T;
    try {
      data = await response.json();
    } catch {
      // JSONパースに失敗した場合
      return {
        ok: false,
        status: response.status,
        error: {
          success: false,
          data: null,
          error: {
            code: "PARSE_ERROR",
            message: "Failed to parse response as JSON",
          },
        },
      };
    }

    if (!response.ok) {
      // バックエンドからのエラーレスポンス
      return {
        ok: false,
        status: response.status,
        error: data as unknown as BackendErrorResponse,
      };
    }

    return {
      ok: true,
      status: response.status,
      data,
    };
  } catch (error) {
    // ネットワークエラーまたはタイムアウト
    const isAbortError = error instanceof Error && error.name === "AbortError";

    return {
      ok: false,
      status: 0,
      error: {
        success: false,
        data: null,
        error: {
          code: isAbortError ? "TIMEOUT" : "NETWORK_ERROR",
          message: isAbortError
            ? `Request timed out after ${timeout}ms`
            : error instanceof Error
              ? error.message
              : "Unknown network error",
        },
      },
    };
  }
}

/**
 * GET リクエスト
 */
export function backendGet<T>(
  endpoint: string,
  options: Omit<BackendFetchOptions, "method" | "body"> = {}
): Promise<BackendResult<T>> {
  return backendFetch<T>(endpoint, { ...options, method: "GET" });
}

/**
 * POST リクエスト
 */
export function backendPost<T>(
  endpoint: string,
  body: unknown,
  options: Omit<BackendFetchOptions, "method" | "body"> = {}
): Promise<BackendResult<T>> {
  return backendFetch<T>(endpoint, {
    ...options,
    method: "POST",
    body: JSON.stringify(body),
  });
}

/**
 * PUT リクエスト
 */
export function backendPut<T>(
  endpoint: string,
  body: unknown,
  options: Omit<BackendFetchOptions, "method" | "body"> = {}
): Promise<BackendResult<T>> {
  return backendFetch<T>(endpoint, {
    ...options,
    method: "PUT",
    body: JSON.stringify(body),
  });
}

/**
 * DELETE リクエスト
 */
export function backendDelete<T>(
  endpoint: string,
  options: Omit<BackendFetchOptions, "method" | "body"> = {}
): Promise<BackendResult<T>> {
  return backendFetch<T>(endpoint, { ...options, method: "DELETE" });
}

/**
 * クエリパラメータを構築
 */
export function buildQueryString(
  params: Record<string, string | number | boolean | undefined | null>
): string {
  const urlParams = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null) {
      urlParams.append(key, String(value));
    }
  }

  const queryString = urlParams.toString();
  return queryString ? `?${queryString}` : "";
}

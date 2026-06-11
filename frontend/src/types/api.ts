/** Standard API response types. */

export interface ApiError {
  code: string;
  message: string;
  details: Record<string, unknown>;
}

export interface ApiMeta {
  total?: number;
  limit?: number;
  offset?: number;
}

export interface ApiResponse<T> {
  data: T | null;
  error: ApiError | null;
  meta: ApiMeta | null;
}

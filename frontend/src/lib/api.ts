import {
  UploadResponse,
  TaskStatusResponse,
  ReportResponse,
  HistoryItem,
} from "./types";

let API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || "";

// If we are in the browser, use relative paths to trigger Vercel's API proxy rewrites
// This avoids CORS issues and double-domain cookie issues.
if (typeof window !== "undefined") {
  API_BASE = "";
} else if (API_BASE && !API_BASE.startsWith("http")) {
  // If running on the server and protocol is missing, auto-fix
  API_BASE = `https://${API_BASE}`;
}

// Strip trailing slash if present
API_BASE = API_BASE.replace(/\/+$/, "");
async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: {
        ...options?.headers,
      },
      credentials: "include",
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    throw new Error(`Network error or server unreachable: ${errorMsg}`);
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      body.detail || `API error ${res.status}: ${res.statusText}`
    );
  }

  return res.json();
}

export async function uploadLogFile(
  file: File,
  userEmail?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiFetch<UploadResponse>("/api/v1/logs/upload", {
    method: "POST",
    body: formData,
    headers: userEmail ? { "X-User-Email": userEmail } : {},
  });
}

export async function getTaskStatus(
  taskId: string,
  userEmail?: string
): Promise<TaskStatusResponse> {
  return apiFetch<TaskStatusResponse>(`/api/v1/logs/status/${taskId}`, {
    headers: userEmail ? { "X-User-Email": userEmail } : {},
  });
}

export async function getReport(
  taskId: string,
  userEmail?: string
): Promise<ReportResponse> {
  return apiFetch<ReportResponse>(`/api/v1/logs/report/${taskId}`, {
    headers: userEmail ? { "X-User-Email": userEmail } : {},
  });
}

export async function getHistory(
  limit: number = 20,
  userEmail?: string
): Promise<{ history: HistoryItem[]; total: number }> {
  return apiFetch(`/api/v1/logs/history?limit=${limit}`, {
    headers: userEmail ? { "X-User-Email": userEmail } : {},
  });
}

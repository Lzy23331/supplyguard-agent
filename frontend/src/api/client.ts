import type {
  AgentEvent,
  ApiResponse,
  DiligenceTaskSummary,
  EvidenceItem,
  ReportResponse,
  ReviewPayload,
  Supplier,
  TaskDetail
} from "../types/diligence";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
      ...options
    });
  } catch {
    throw new Error(`无法连接后端，请确认 FastAPI 已运行在 ${API_BASE_URL}`);
  }

  const body = (await response.json().catch(() => null)) as ApiResponse<T> | null;
  if (!response.ok || !body) {
    throw new Error(body?.error?.message || `请求失败：HTTP ${response.status}`);
  }
  if (body.success === false) {
    throw new Error(body.error?.message || "接口返回失败");
  }
  return body.data as T;
}

export const api = {
  getSampleSuppliers: () => request<Supplier[]>("/api/samples/suppliers"),
  createTaskFromSample: (supplierId: string) =>
    request<DiligenceTaskSummary>(`/api/diligence/tasks/from-sample/${supplierId}`, { method: "POST" }),
  createCustomTask: (supplier: Supplier) =>
    request<DiligenceTaskSummary>("/api/diligence/tasks", { method: "POST", body: JSON.stringify({ supplier }) }),
  getTasks: () => request<DiligenceTaskSummary[]>("/api/diligence/tasks"),
  getTask: (taskId: string) => request<TaskDetail>(`/api/diligence/tasks/${taskId}`),
  getTaskEvents: (taskId: string) => request<AgentEvent[]>(`/api/diligence/tasks/${taskId}/events`),
  getTaskEvidence: (taskId: string) => request<EvidenceItem[]>(`/api/diligence/tasks/${taskId}/evidence`),
  getTaskReport: (taskId: string) => request<ReportResponse>(`/api/diligence/tasks/${taskId}/report`),
  submitReview: (taskId: string, payload: ReviewPayload) =>
    request<{ task_id: string; decision: string; created_at: string }>(`/api/diligence/tasks/${taskId}/review`, {
      method: "POST",
      body: JSON.stringify(payload)
    })
};

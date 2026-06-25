import type {
  AgentEvent,
  ApiResponse,
  DemoCasePreview,
  DemoCaseSummary,
  DiligenceTaskSummary,
  EvidenceItem,
  ExecutionMode,
  ProviderStatus,
  ReportResponse,
  TaskDiagnostics,
  ReviewPayload,
  Supplier,
  TaskDetail,
  UploadMaterial,
} from "../types/diligence";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  const isFormData = options?.body instanceof FormData;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { ...(isFormData ? {} : { "Content-Type": "application/json" }), ...(options?.headers ?? {}) },
      ...options,
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


async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`请求失败：HTTP ${response.status}`);
  }
  return response.blob();
}
async function requestOrNull<T>(path: string): Promise<T | null> {
  try {
    return await request<T>(path);
  } catch {
    return null;
  }
}

export const api = {
  getProviderStatus: () => request<ProviderStatus>("/api/system/provider-status"),
  getDemoCases: () => request<DemoCaseSummary[]>("/api/demo-cases"),
  getDemoCasePreview: (caseId: string) => request<DemoCasePreview>(`/api/demo-cases/${caseId}/preview`),
  runDemoCase: (caseId: string) => request<TaskDetail>(`/api/demo-cases/${caseId}/run`, { method: "POST" }),
  getSampleSuppliers: () => request<Supplier[]>("/api/samples/suppliers"),
  createTaskFromSample: (supplierId: string, executionMode: ExecutionMode = "async") =>
    request<DiligenceTaskSummary>(`/api/diligence/tasks/from-sample/${supplierId}?execution_mode=${executionMode}`, { method: "POST" }),
  createCustomTask: (supplier: Supplier, executionMode: ExecutionMode = "async") =>
    request<DiligenceTaskSummary>("/api/diligence/tasks", { method: "POST", body: JSON.stringify({ supplier, execution_mode: executionMode }) }),
  createDiligenceTask: (payload: { supplier?: Supplier; supplier_id?: string; company_name?: string; procurement_amount?: number; cooperation_type?: string; execution_mode?: ExecutionMode; material_text?: string; upload_ids?: string[] }) =>
    request<DiligenceTaskSummary>("/api/diligence/tasks", { method: "POST", body: JSON.stringify(payload) }),
  uploadMaterial: async (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return request<UploadMaterial>("/api/uploads/materials", { method: "POST", body, headers: {} });
  },
  getTasks: () => request<DiligenceTaskSummary[]>("/api/diligence/tasks"),
  getTask: (taskId: string) => request<TaskDetail>(`/api/diligence/tasks/${taskId}`),
  getDiligenceTask: (taskId: string) => request<TaskDetail>(`/api/diligence/tasks/${taskId}`),
  getTaskEvents: (taskId: string) => request<AgentEvent[]>(`/api/diligence/tasks/${taskId}/events`),
  getDiligenceTaskEvents: (taskId: string) => request<AgentEvent[]>(`/api/diligence/tasks/${taskId}/events`),
  getTaskEvidence: (taskId: string) => request<EvidenceItem[]>(`/api/diligence/tasks/${taskId}/evidence`),
  getTaskReport: (taskId: string) => request<ReportResponse>(`/api/diligence/tasks/${taskId}/report`),
  getTaskReportPdf: (taskId: string) => requestBlob(`/api/diligence/tasks/${taskId}/report.pdf`),
  getDiligenceTaskReport: (taskId: string) => requestOrNull<ReportResponse>(`/api/diligence/tasks/${taskId}/report`),
  getTaskDiagnostics: (taskId: string) => request<TaskDiagnostics>(`/api/diligence/tasks/${taskId}/diagnostics`),
  submitReview: (taskId: string, payload: ReviewPayload) =>
    request<{ task_id: string; decision: string; created_at: string }>(`/api/diligence/tasks/${taskId}/review`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};



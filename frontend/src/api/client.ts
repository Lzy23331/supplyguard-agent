export type SupplierInput = {
  name: string;
  website?: string;
  industry: string;
  region: string;
  annual_spend: number;
  cooperation_type: string;
  sample_key?: string;
};

export type DiligenceTask = {
  id: string;
  status: string;
  supplier: SupplierInput;
  risk_level?: string;
  total_score?: number;
  recommendation?: string;
  dimensions: Array<{ dimension: string; score: number; level: string; rationale: string }>;
  evidence: Array<{ title: string; content: string; source: string; severity: string; url?: string }>;
  created_at: string;
  updated_at: string;
};

export type AgentEvent = {
  id: number;
  agent_name: string;
  status: string;
  summary: string;
  tool_calls: Array<Record<string, unknown>>;
  created_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  samples: () => request<SupplierInput[]>("/api/samples/suppliers"),
  createTask: (supplier: SupplierInput) =>
    request<DiligenceTask>("/api/diligence/tasks", { method: "POST", body: JSON.stringify({ supplier }) }),
  getTask: (taskId: string) => request<DiligenceTask>(`/api/diligence/tasks/${taskId}`),
  getEvents: (taskId: string) => request<AgentEvent[]>(`/api/diligence/tasks/${taskId}/events`),
  getReport: (taskId: string) => request<{ task_id: string; markdown: string }>(`/api/diligence/tasks/${taskId}/report`)
};


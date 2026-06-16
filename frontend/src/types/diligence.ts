export type RiskLevel = "low" | "medium" | "high";

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  message?: string;
  error?: { code: string; message: string; details?: unknown };
};

export type Supplier = {
  id?: string;
  sample_key?: string;
  name: string;
  website?: string;
  industry?: string;
  region?: string;
  annual_spend?: number;
  procurement_amount?: number;
  cooperation_type?: string;
  business_status?: string;
  company_age_years?: number;
  profile_completeness?: string;
  ownership_transparency?: string;
  urgency?: string;
  summary?: string;
  tags?: string[];
  expected_risk_level?: RiskLevel;
};

export type DiligenceTaskSummary = {
  task_id: string;
  status: string;
  supplier_id?: string;
  supplier_name?: string;
  risk_level?: RiskLevel;
  raw_score?: number;
  total_score?: number;
  recommendation?: string;
  summary?: string;
  created_at?: string;
  updated_at?: string;
};

export type RiskRule = {
  rule_id?: string;
  rule_name?: string;
  dimension?: string;
  score?: number;
  reason?: string;
  evidence_ids?: string[];
};

export type RiskAssessment = {
  raw_score?: number;
  total_score?: number;
  risk_level?: RiskLevel;
  dimension_scores?: Record<string, number>;
  triggered_rules?: RiskRule[];
  recommendation?: string;
};

export type TaskDetail = {
  task: { id: string; status: string; summary?: string; created_at?: string; updated_at?: string };
  supplier: Supplier;
  risk_assessment: RiskAssessment;
  evidence_count?: number;
  event_count?: number;
};

export type AgentEvent = {
  id: number;
  task_id: string;
  agent_name: string;
  event_type?: string;
  status: string;
  summary: string;
  tool_name?: string;
  tool_input?: unknown;
  tool_output_summary?: string;
  created_at: string;
};

export type EvidenceItem = {
  id?: string;
  source: string;
  category?: string;
  title: string;
  content: string;
  severity: string;
  rule_signals?: string[];
  economic_rationale?: string;
  url?: string;
  created_at?: string;
};

export type ReportResponse = {
  task_id: string;
  markdown_content: string;
};

export type ReviewPayload = {
  reviewer: string;
  decision: "approve" | "approve_with_conditions" | "reject" | "escalate";
  comment?: string;
};

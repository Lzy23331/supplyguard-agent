export type RiskLevel = "low" | "medium" | "high";
export type TaskStatus = "pending" | "running" | "completed" | "failed" | "reviewed";
export type ExecutionMode = "sync" | "async";

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
  id?: string;
  status: TaskStatus;
  supplier_id?: string;
  supplier_name?: string;
  risk_level?: RiskLevel | null;
  raw_score?: number | null;
  total_score?: number | null;
  recommendation?: string | null;
  error_message?: string | null;
  summary?: string;
  created_at?: string;
  updated_at?: string;
  cooperation_type?: string | null;
  procurement_amount?: number | null;
  provider_mode?: string | null;
  search_query_count?: number;
  web_search_result_count?: number;
  real_url_count?: number;
  profile_snapshot_count?: number;
  profile_non_empty_count?: number;
  scoring_evidence_count?: number;
  report_available?: boolean;
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
  raw_score?: number | null;
  total_score?: number | null;
  risk_level?: RiskLevel | null;
  dimension_scores?: Record<string, number>;
  triggered_rules?: RiskRule[];
  recommendation?: string | null;
};

export type CompanyProfileSnapshot = {
  id?: number;
  task_id?: string;
  supplier_id?: string;
  company_name?: string;
  field_name: string;
  field_value?: string | null;
  confidence?: number | null;
  source_type?: string;
  source_name?: string;
  source_url?: string | null;
  query?: string | null;
  extraction_method?: string | null;
  requires_manual_verification?: boolean;
  reason?: string | null;
  metadata_json?: Record<string, unknown>;
  created_at?: string;
};


export type WebSearchResultPreview = {
  id?: number;
  task_id?: string;
  query?: string | null;
  title?: string | null;
  url?: string | null;
  snippet?: string | null;
  rank?: number | null;
  source_name?: string | null;
  domain_trust_score?: number | null;
  entity_match_score?: number | null;
  decision?: string | null;
  decision_reason?: string | null;
  matched_risk_keywords?: string[];
  metadata_json?: Record<string, unknown>;
};

export type TaskDiagnostics = {
  task_id: string;
  provider_mode?: string | null;
  search_query_count: number;
  web_search_result_count: number;
  real_url_count: number;
  profile_snapshot_count: number;
  profile_non_empty_count: number;
  scoring_evidence_count: number;
  evidence_item_count?: number;
  report_available: boolean;
  web_search_results_preview?: WebSearchResultPreview[];
  company_profile_preview?: CompanyProfileSnapshot[];
};
export type TaskDetail = {
  id?: string;
  task_id?: string;
  status?: TaskStatus;
  supplier_id?: string;
  risk_level?: RiskLevel | null;
  total_score?: number | null;
  recommendation?: string | null;
  error_message?: string | null;
  task: { id: string; status: TaskStatus; summary?: string; error_message?: string | null; created_at?: string; updated_at?: string };
  supplier: Supplier;
  risk_assessment: RiskAssessment;
  evidence_count?: number;
  event_count?: number;
  company_profile?: CompanyProfileSnapshot[];
  web_search_results?: WebSearchResultPreview[];
  diagnostics?: TaskDiagnostics;
  provider_mode?: string | null;
  search_query_count?: number;
  web_search_result_count?: number;
  real_url_count?: number;
  profile_snapshot_count?: number;
  profile_non_empty_count?: number;
  scoring_evidence_count?: number;
  report_available?: boolean;
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
  risk_keywords?: string[];
  economic_rationale?: string;
  url?: string;
  source_url?: string;
  source_type?: "mock_sample" | "user_input" | "uploaded_file" | "external_api" | string;
  source_name?: string;
  confidence?: number | null;
  raw_text?: string | null;
  normalized_content?: string | null;
  extracted_by?: string | null;
  should_use_for_scoring?: boolean | number | null;
  metadata_json?: Record<string, unknown>;
  created_at?: string;
};

export type UploadMaterial = {
  upload_id: string;
  filename: string;
  file_type?: string;
  status: "uploaded" | "parsed" | "failed";
  text_length?: number;
  summary?: string | null;
  error_message?: string | null;
};

export type ReportResponse = {
  task_id: string;
  markdown_content: string;
  filename?: string;
};

export type ReviewPayload = {
  reviewer: string;
  decision: "approve" | "approve_with_conditions" | "reject" | "escalate";
  comment?: string;
};




export type DemoCaseSummary = {
  case_id: string;
  company_name: string;
  description?: string;
  industry?: string;
  region?: string;
  risk_level?: RiskLevel;
  score?: number;
  web_search_results_count: number;
  real_url_count: number;
  profile_field_count: number;
  report_available: boolean;
  cached_demo: boolean;
};

export type DemoCasePreview = DemoCaseSummary & {
  search_queries?: string[];
  web_search_results_preview?: WebSearchResultPreview[];
  company_profile_preview?: Record<string, string | null>;
};

export type ProviderStatus = {
  deployment_mode: string;
  real_query_enabled: boolean;
  real_query_requested?: boolean;
  tencent_search_configured: boolean;
  llm_configured: boolean;
  pdf_export_available: boolean;
  demo_mode_available: boolean;
  web_search_provider?: string;
  web_search_api?: string;
  llm_model?: string | null;
};

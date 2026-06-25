# Agent Engineering

## Agent Design

The workflow uses a shared structured context instead of loose text passing. This keeps each step explainable and testable.

- `IntakeAgent` creates a diligence plan from supplier attributes, then asks `LLMTaskService` for a structured plan with mock fallback.
- `EvidenceCollectorAgent` collects mock public evidence and stores it.
- `MaterialAnalysisAgent` extracts structured risk evidence from optional user-pasted material.
- `ComplianceRiskAgent` retrieves policies and applies risk rules.
- `BusinessRiskAgent` records operating, delivery, completeness and reputation dimensions.
- `ReportAgent` produces a Markdown report.

The same `Orchestrator` is used by sync and async execution. Async mode only changes who starts the workflow: a FastAPI background task loads the task and supplier again, sets status to `running`, calls the orchestrator, then records `completed` or `failed`.

Sample suppliers and custom suppliers share the same orchestrator. Custom supplier input only changes how the supplier record is created; downstream planning, material analysis, policy retrieval, rule scoring and report generation are reused.

## Tool Design

Tools represent capabilities that could later be replaced by production services:

- `MockSearchTool`: local deterministic public search.
- `DocumentParserTool`: Markdown/TXT policy loading.
- `RAGPolicyTool`: keyword-scored policy retrieval from `data/policies`.
- `LLMTaskService`: unified LLM task wrapper for intake planning and policy query rewrite.
- `MockLLMClient`: deterministic no-key implementation for stable demos.
- `OpenAICompatibleClient`: OpenAI/DeepSeek-compatible Chat Completions client.
- `RiskRuleTool`: explainable risk scoring with `raw_score`, `total_score`, `risk_level` and `hit_rules`.
- `EvidenceStoreTool`: evidence persistence.
- `EvidenceExtractionTool`: LLM-first user material evidence extraction with keyword fallback.
- `ReportExportTool`: report generation.

## Risk Level Contract

Internal risk levels are lowercase strings: `low`, `medium`, `high`. User-facing surfaces can display them as 低风险、中风险、高风险.

`raw_score` is the sum of triggered rules. `total_score` is capped with `min(raw_score, 100)`. This lets high-risk reports explain why a supplier reached 100 without hiding the original cumulative exposure.

## RAG, Memory and Context

The v1 RAG implementation is deliberately simple: split policy Markdown into chunks and rank by query-term matches. Policy documents include keyword lines so high-risk suppliers retrieve 制裁名单、黑名单、境外供应商、升级审批 snippets, while medium-risk suppliers retrieve 交付延期、合同争议、补充材料、人工复核 snippets.

The LLM enhancement only rewrites search queries before this local retrieval step. It does not create policy content and cannot change scores.

User-pasted material is handled before risk scoring. Extracted evidence is saved with `source_type=user_input`, source quote, confidence and metadata. Low-confidence or explicitly excluded evidence can set `should_use_for_scoring=false`; `RiskRuleTool` ignores it.

Uploaded materials use the same evidence path. `FileParserTool` extracts text from txt/md/csv/pdf, `MaterialAnalysisAgent` sends parsed text to `EvidenceExtractionTool`, and saved evidence uses `source_type=uploaded_file`. Word files, OCR and external APIs remain out of scope.

Memory is persisted in SQLite rather than hidden inside prompts. Agent events, evidence, risk assessments and reports can all be inspected from API responses.

## Model Strategy

The default mode is `mock`, which makes the demo stable offline. `llm` mode calls an OpenAI-compatible endpoint when credentials are available. `DEEPSEEK_API_KEY` is supported as a local environment alias for DeepSeek demos.

Every LLM task writes `llm_call_logs` with task type, prompt name, model mode, summaries, success/fallback state and latency. The model never decides the risk score, risk level or recommendation.

## Evaluation

The test suite validates task creation, sync and async execution modes, low/medium/high sample differentiation, medium score stability, high raw-score capping, agent event persistence, report content, policy retrieval, LLM mock/fallback behavior and high-risk rule hits.
# 第八批：联网搜索计划与腾讯云 Provider

企业名称查询任务现在会在 `CompanyResolverAgent` 后执行 `SearchQueryPlannerAgent`。该 Agent 最多调用一次 LLM 生成 5-8 条尽调搜索 query；失败时回退模板 query。`TencentWebSearchProvider` 读取 query 计划后调用腾讯云联网搜索，并只处理 title、snippet/summary、URL。`SearchResultEvidenceExtractor` 负责把明确风险词转为 `source_type=web_search` 证据，再交给规则引擎统一评分。

设计约束：

- 不抓取网页正文。
- 不让 LLM 或 Provider 输出最终风险等级。
- 单条 query 失败只写 warning 并继续。
- 全部 query 失败时由 ProviderManager fallback 到 mock provider。
- API Key 不写入日志、事件、报告或测试。

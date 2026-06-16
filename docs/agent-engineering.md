# Agent Engineering

## Agent Design

The workflow uses a shared structured context instead of loose text passing. This keeps each step explainable and testable.

- `IntakeAgent` creates a diligence plan from supplier attributes.
- `EvidenceCollectorAgent` collects mock public evidence and stores it.
- `ComplianceRiskAgent` retrieves policies and applies risk rules.
- `BusinessRiskAgent` records operating, delivery, completeness and reputation dimensions.
- `ReportAgent` produces a Markdown report.

## Tool Design

Tools represent capabilities that could later be replaced by production services:

- `MockSearchTool`: local deterministic public search.
- `DocumentParserTool`: Markdown/TXT policy loading.
- `RAGPolicyTool`: keyword-scored policy retrieval from `data/policies`.
- `RiskRuleTool`: explainable risk scoring with `raw_score`, `total_score`, `risk_level` and `hit_rules`.
- `EvidenceStoreTool`: evidence persistence.
- `ReportExportTool`: report generation.

## Risk Level Contract

Internal risk levels are lowercase strings: `low`, `medium`, `high`. User-facing surfaces can display them as 低风险、中风险、高风险.

`raw_score` is the sum of triggered rules. `total_score` is capped with `min(raw_score, 100)`. This lets high-risk reports explain why a supplier reached 100 without hiding the original cumulative exposure.

## RAG, Memory and Context

The v1 RAG implementation is deliberately simple: split policy Markdown into chunks and rank by query-term matches. Policy documents include keyword lines so high-risk suppliers retrieve 制裁名单、黑名单、境外供应商、升级审批 snippets, while medium-risk suppliers retrieve 交付延期、合同争议、补充材料、人工复核 snippets.

Memory is persisted in SQLite rather than hidden inside prompts. Agent events, evidence, risk assessments and reports can all be inspected from API responses.

## Model Strategy

The default mode is `mock`, which makes the demo stable offline. `llm` mode is only an extension point. The first version does not require an LLM for correctness, and the model never decides the risk score.

## Evaluation

The test suite validates task creation, low/medium/high sample differentiation, medium score stability, high raw-score capping, agent event persistence, report content, policy retrieval and high-risk rule hits.

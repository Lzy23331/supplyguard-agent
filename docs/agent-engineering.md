# Agent Engineering

## Agent Design

The workflow uses a shared structured context instead of loose text passing. This keeps each step explainable and testable.

- `IntakeAgent` creates a diligence plan from supplier attributes.
- `EvidenceCollectorAgent` collects mock public evidence and stores it.
- `ComplianceRiskAgent` retrieves policies and applies risk rules.
- `BusinessRiskAgent` records operating and delivery risk dimensions.
- `ReportAgent` produces a Markdown report.

## Tool Design

Tools represent capabilities that could later be replaced by production services:

- `MockSearchTool`: local deterministic public search.
- `DocumentParserTool`: Markdown/TXT policy loading.
- `RAGPolicyTool`: keyword-scored policy retrieval.
- `RiskRuleTool`: explainable risk scoring.
- `EvidenceStoreTool`: evidence persistence.
- `ReportExportTool`: report generation.

## RAG, Memory and Context

The v1 RAG implementation is deliberately simple: split policy Markdown into chunks and rank by query-term matches. For a portfolio project, this is useful because the reasoning is inspectable.

Memory is persisted in SQLite rather than hidden inside prompts. Agent events, evidence, risk assessments and reports can all be inspected from API responses.

## Model Strategy

The default mode is `mock`, which makes the demo stable offline. `llm` mode keeps an OpenAI-compatible extension point for DeepSeek, Qwen or OpenAI. The first version does not require an LLM for correctness.

## Evaluation

The test suite validates:

- Task creation.
- Low, medium and high sample differentiation.
- Agent event persistence.
- Report content.
- Policy retrieval.
- High-risk rule hits.


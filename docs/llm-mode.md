# LLM Mode

## Usage Boundary

LLM is an assistant layer, not the final decision maker. It can generate an intake plan and policy search queries, but it cannot decide `total_score`, `risk_level`, `dimension_scores`, `triggered_rules` or `recommendation`.

LLM must not invent evidence, policy text or external search results.

## Call Chain

1. `IntakeAgent` calls `LLMTaskService.generate_intake_plan`.
2. `RAGPolicyTool` calls `LLMTaskService.rewrite_policy_queries`.
3. `EvidenceExtractionTool` can call the same LLM client for `evidence_extraction`.
4. `LLMTaskService` or the tool gets a client from `llm_factory`.
5. The factory returns `MockLLMClient` or `OpenAICompatibleClient`.
6. Outputs are validated or normalized before entering the workflow.
7. `llm_audit_service` writes `llm_call_logs`.

## Client Modes

`MockLLMClient` is deterministic and requires no API Key. It supports stable demos, tests and interviews.

`OpenAICompatibleClient` calls `{OPENAI_BASE_URL}/chat/completions` with `OPENAI_MODEL` and `OPENAI_API_KEY`. It is compatible with OpenAI, DeepSeek and similar providers.

If `DEEPSEEK_API_KEY` exists and `OPENAI_API_KEY` is empty, the backend uses it automatically. When no explicit base URL or model is set, it uses `https://api.deepseek.com/v1` and `deepseek-chat`.

## Fallback

When `LLM_FALLBACK_TO_MOCK=true`, failures fall back to `MockLLMClient`. Fallback covers missing key, request failure, timeout and invalid JSON.

Fallback is logged. The main task should keep running unless both the real call and fallback fail.

## llm_call_logs

The `llm_call_logs` table stores:

- task and agent identity
- LLM task type
- requested/actual model mode and model name
- prompt name
- short input and output summaries
- success state
- fallback state and reason
- error message
- latency

The table intentionally does not store API Keys or full long prompts.

## Why Logs Matter

LLM logs make demos explainable: reviewers can see when a model was used, whether fallback happened, and what structured output entered the workflow.

They also support debugging without exposing secrets.

## Why RiskRuleTool Still Decides Risk

Supplier risk needs deterministic, auditable behavior. `RiskRuleTool` owns scoring and recommendations so sample suppliers remain stable:

- low stays low
- medium stays medium
- high stays high

LLM output can improve planning and retrieval context, but it cannot override rule results.

For user material analysis, LLM output must include a `source_quote`; evidence without a quote is discarded. If the LLM fails or returns invalid JSON, keyword fallback extracts only deterministic terms such as 制裁、黑名单、交付延期、付款纠纷、合同争议 and 资料缺失.

## Later Batches

Future batches can add `EvidenceExtractionAgent`, `PolicyInterpretationAgent`, `MissingInfoAgent`, `ReportQualityAgent`, `ReportChatAgent`, `CompanyResolverAgent` and an `EvidenceProvider` abstraction layer.

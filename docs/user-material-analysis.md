# User Material Analysis

## Purpose

Users can paste supplier-related material when creating a task. Examples include website descriptions, news snippets, delivery delay notes, contract dispute summaries or internal procurement notes.

The material is optional. Empty material keeps the original sample supplier workflow unchanged.

## Extraction Flow

1. `TaskCreate.material_text` stores the pasted text on the task.
2. `MaterialAnalysisAgent` runs after mock evidence collection and before risk scoring.
3. `EvidenceExtractionTool` tries LLM extraction when `MODEL_MODE=llm`.
4. If LLM extraction fails, times out or returns invalid JSON, keyword fallback is used.
5. Extracted items are saved to `evidence_items` with `source_type=user_input`.

## source_quote

Every LLM-extracted item must include `source_quote`. The quote anchors the evidence to the original user material and prevents unsupported claims from entering the evidence chain.

Evidence without a source quote is discarded.

## Fallback Keywords

The deterministic fallback covers terms such as 制裁、黑名单、重大失信、行政处罚、经营异常、交付延期、付款纠纷、合同争议、负面新闻、资料缺失、官网缺失 and 成立时间短.

## Boundary

User material evidence only reflects what the user pasted. It does not represent complete due diligence and does not replace public evidence, policy review or human review.

LLM does not decide the final risk score or risk level. `RiskRuleTool` remains the only final scoring path.

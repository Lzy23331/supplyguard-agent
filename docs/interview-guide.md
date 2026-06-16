# Interview Guide

## 60-Second Pitch

SupplyGuard Agent is a supplier onboarding due diligence system. It turns a real procurement compliance workflow into an agent pipeline: parse supplier input, collect evidence, retrieve policy rules, score compliance and business risks, and generate a review-ready report with an audit trail.

## Demo Path

1. Start the backend and frontend from `D:\projects\supplyguard-agent`.
2. Open the workbench.
3. Run the `low` supplier and show the approval recommendation.
4. Run the `medium` supplier and show supplementary document and human review requirements.
5. Run the `high` supplier and show sanctions/blacklist evidence, `raw_score` above 100, capped `total_score` of 100 and escalation recommendation.
6. Open the timeline to explain agent observability.
7. Open the report to show evidence-linked decision output.

## Technical Talking Points

- The project uses deterministic mock data so interviewers can reproduce the same results.
- Internal risk levels are `low`, `medium`, `high`; display labels are 低风险、中风险、高风险.
- Agent events make the workflow observable and debuggable.
- Tools are separated from agents, so mock search can become real search later.
- RAG is policy-based and explainable, not a black-box claim.
- SQLite creates a simple audit trail for evidence, ratings and reviews.

## Extension Ideas

- Add async job execution and SSE/WebSocket streaming.
- Connect real sanctions, business registry and adverse media APIs.
- Add document parsing for supplier certificates and contracts.
- Add evaluation metrics for risk rating consistency.
- Add reviewer roles, approval workflow and exportable audit packs.

from typing import Any


class ReportExportTool:
    name = "ReportExportTool"

    def build_markdown(
        self,
        supplier: dict[str, Any],
        plan: dict[str, Any],
        evidence: list[dict[str, Any]],
        risk: dict[str, Any],
        policies: list[dict[str, Any]],
    ) -> str:
        evidence_lines = "\n".join(
            f"- **{item['title']}** [{item.get('severity', 'info')}]: {item['content']}" for item in evidence
        )
        dimension_lines = "\n".join(
            f"| {d['dimension']} | {d['score']} | {d['level']} | {d['rationale']} |" for d in risk["dimensions"]
        )
        policy_lines = "\n".join(f"- `{p['document']}`: {p['chunk'][:180]}..." for p in policies) or "- No policy match."
        return f"""# Supplier Due Diligence Report: {supplier['name']}

## Executive Summary

- Risk level: **{risk['risk_level']}**
- Total score: **{risk['total_score']} / 100**
- Recommendation: **{risk['recommendation']}**
- Scope: {', '.join(plan['checks'])}

## Supplier Profile

- Website: {supplier.get('website') or 'N/A'}
- Industry: {supplier.get('industry')}
- Region: {supplier.get('region')}
- Annual spend: {supplier.get('annual_spend')}
- Cooperation type: {supplier.get('cooperation_type')}

## Risk Assessment

| Dimension | Score | Level | Rationale |
| --- | ---: | --- | --- |
{dimension_lines}

## Evidence Chain

{evidence_lines}

## Policy References

{policy_lines}

## Human Review Suggestion

{risk['recommendation']}
"""


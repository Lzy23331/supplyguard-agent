from typing import Any


class RiskRuleTool:
    name = "RiskRuleTool"

    HIGH_TERMS = ["sanction", "制裁", "bribery", "贿赂", "fraud", "失信", "blacklist", "拒绝"]
    MEDIUM_TERMS = ["lawsuit", "诉讼", "经营异常", "late delivery", "延期", "negative", "补充材料"]

    def assess(self, evidence: list[dict[str, Any]], supplier: dict[str, Any]) -> dict[str, Any]:
        compliance = 12
        business = 10
        delivery = 8
        for item in evidence:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            severity = item.get("severity", "info")
            if severity == "critical" or any(term in text for term in self.HIGH_TERMS):
                compliance += 45
                business += 25
                delivery += 30
            elif severity == "warning" or any(term in text for term in self.MEDIUM_TERMS):
                compliance += 18
                business += 22
                delivery += 8
        if supplier.get("annual_spend", 0) >= 1000000:
            business += 8
        dimensions = [
            self._dimension("Compliance", compliance, "Sanctions, integrity, litigation and onboarding policy checks."),
            self._dimension("Business", business, "Operating stability, public reputation and contract exposure."),
            self._dimension("Delivery", delivery, "Continuity, timeliness and procurement execution risk."),
        ]
        total = min(100, round(sum(d["score"] for d in dimensions) / len(dimensions)))
        level = self._level(total)
        recommendation = {
            "Low": "Approve onboarding with standard annual monitoring.",
            "Medium": "Conditionally approve after supplementary documents and manager review.",
            "High": "Reject onboarding or escalate to compliance committee before any purchase order.",
        }[level]
        return {"total_score": total, "risk_level": level, "recommendation": recommendation, "dimensions": dimensions}

    def _dimension(self, name: str, score: int, rationale: str) -> dict[str, Any]:
        bounded = max(0, min(100, score))
        return {"dimension": name, "score": bounded, "level": self._level(bounded), "rationale": rationale}

    def _level(self, score: int) -> str:
        if score >= 70:
            return "High"
        if score >= 35:
            return "Medium"
        return "Low"

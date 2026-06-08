from typing import Any


class RiskRuleTool:
    name = "RiskRuleTool"

    HIGH_TERMS = ["sanction", "制裁", "bribery", "贿赂", "fraud", "失信", "blacklist", "拒绝", "watchlist"]
    MEDIUM_TERMS = ["lawsuit", "诉讼", "经营异常", "late delivery", "延期", "补充材料", "dispute"]

    def assess(self, evidence: list[dict[str, Any]], supplier: dict[str, Any]) -> dict[str, Any]:
        compliance = 12
        business = 10
        delivery = 8
        has_critical = False
        for item in evidence:
            text = f"{item.get('title', '')} {item.get('content', '')}".lower()
            severity = item.get("severity", "info")
            if severity == "critical" or (severity != "info" and any(term in text for term in self.HIGH_TERMS)):
                has_critical = True
                compliance += 70
                business += 65
                delivery += 62
            elif severity == "warning" or (severity != "info" and any(term in text for term in self.MEDIUM_TERMS)):
                compliance += 18
                business += 22
                delivery += 8
        if supplier.get("annual_spend", 0) >= 1000000:
            business += 8
        dimensions = [
            self._dimension("Compliance", compliance, "覆盖制裁、商业诚信、诉讼记录与供应商准入政策检查。"),
            self._dimension("Business", business, "评估经营稳定性、公开舆情、采购金额暴露与合作必要性。"),
            self._dimension("Delivery", delivery, "评估供应连续性、交付及时性与采购执行风险。"),
        ]
        total = min(100, round(sum(d["score"] for d in dimensions) / len(dimensions)))
        level = "High" if has_critical else self._level(total)
        recommendation = {
            "Low": "建议准入，按标准年度监控机制持续跟踪。",
            "Medium": "建议补充材料并完成业务负责人复核后有条件准入。",
            "High": "建议拒绝准入，或在任何采购订单前升级至合规委员会审批。",
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

import json
import re
from typing import Any

from app.llm.base import BaseLLMClient


def _unique_limited(items: list[str], minimum: int = 0, maximum: int = 6) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result[:maximum] if len(result) >= minimum else result


class MockLLMClient(BaseLLMClient):
    model_name = "mock-llm"

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> dict:
        payload = self._parse_payload(user_prompt)
        if task_type == "intake_plan":
            return self._intake_plan(payload.get("supplier_profile", payload))
        if task_type == "policy_query_rewrite":
            return self._policy_query_rewrite(payload)
        if task_type == "search_query_plan":
            return self._search_query_plan(payload.get("supplier_profile", payload))
        return {}

    def complete_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        task_type: str,
        timeout_seconds: int | None = None,
    ) -> str:
        return json.dumps(
            self.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                task_type=task_type,
                timeout_seconds=timeout_seconds,
            ),
            ensure_ascii=False,
        )

    def _parse_payload(self, user_prompt: str) -> dict[str, Any]:
        try:
            return json.loads(user_prompt)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", user_prompt, flags=re.S)
            if not match:
                return {}
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}

    def _intake_plan(self, supplier: dict[str, Any]) -> dict[str, list[str]]:
        focus_areas = ["合规风险", "经营风险", "交付风险", "资料完整性"]
        suggested_tools = ["MockSearchTool", "RAGPolicyTool", "RiskRuleTool"]
        risk_hypotheses = ["根据供应商地区、采购金额、合作类型和资料完整性生成初步风险假设"]
        questions = [
            "是否已完成供应商基础信息核验？",
            "是否存在负面舆情、行政处罚、失信或黑名单风险？",
            "是否需要补充准入材料？",
        ]

        region = str(supplier.get("region") or "")
        cooperation_type = str(supplier.get("cooperation_type") or supplier.get("urgency") or "")
        business_status = str(supplier.get("business_status") or "")
        completeness = str(supplier.get("profile_completeness") or "")
        procurement_amount = supplier.get("procurement_amount") or supplier.get("annual_spend") or 0

        if "境外" in region:
            focus_areas.extend(["境外供应商审查", "制裁风险"])
        if "紧急" in cooperation_type:
            focus_areas.append("紧急采购风险")
        if float(procurement_amount or 0) >= 3000000:
            risk_hypotheses.append("采购金额较高，建议关注审批层级和付款风险")
        if completeness == "低":
            questions.append("是否已补充注册证明、合规声明和联系人信息？")
        if "异常" in business_status or "不透明" in business_status:
            focus_areas.append("主体信息透明度")

        return {
            "focus_areas": _unique_limited(focus_areas, maximum=8),
            "suggested_tools": suggested_tools,
            "risk_hypotheses": _unique_limited(risk_hypotheses, maximum=6),
            "questions_for_review": _unique_limited(questions, maximum=6),
        }

    def _policy_query_rewrite(self, payload: dict[str, Any]) -> dict[str, list[str]]:
        supplier = payload.get("supplier_profile") or {}
        evidence_keywords = payload.get("evidence_keywords") or []
        keyword_text = " ".join(str(item) for item in evidence_keywords)
        queries = [
            "供应商准入 资料完整性 审查要求",
            "供应商风险评分 人工复核 准入建议",
            "黑名单 制裁名单 合规审查",
            "交付延期 合同争议 采购复核",
        ]
        if "制裁" in keyword_text or "黑名单" in keyword_text:
            queries.extend(["制裁名单 黑名单 升级审批", "合规风险 高风险供应商 准入限制"])
        if "境外" in str(supplier.get("region") or ""):
            queries.append("境外供应商 合规审查 制裁筛查")
        if "紧急" in str(supplier.get("cooperation_type") or supplier.get("urgency") or ""):
            queries.append("紧急采购 高额采购 人工复核")
        if "交付延期" in keyword_text or "合同争议" in keyword_text:
            queries.append("交付延期 合同争议 供应商复核")
        return {"queries": _unique_limited(queries, minimum=3, maximum=6)}

    def _search_query_plan(self, supplier: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
        company = supplier.get("company_name") or supplier.get("name") or "供应商"
        queries = [
            {"query": f"{company} 行政处罚 经营异常", "purpose": "business_risk"},
            {"query": f"{company} 失信 被执行人 限制高消费", "purpose": "legal_risk"},
            {"query": f"{company} 诉讼 合同纠纷 付款纠纷", "purpose": "dispute_risk"},
            {"query": f"{company} 黑名单 制裁 违规", "purpose": "compliance_risk"},
            {"query": f"{company} 注册资本 成立时间 统一社会信用代码", "purpose": "company_profile"},
            {"query": f"{company} 质量问题 交付延期 投诉", "purpose": "delivery_risk"},
        ]
        return {"queries": queries}

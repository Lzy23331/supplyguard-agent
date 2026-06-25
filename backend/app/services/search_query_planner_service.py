from typing import Any

from app.config import get_settings
from app.database import get_db
from app.services.llm_task_service import generate_search_query_plan


class SearchQueryPlannerService:
    def plan(self, task_id: str, supplier: dict[str, Any]) -> list[dict[str, str]]:
        if get_settings().llm_query_planner_enabled:
            with get_db() as db:
                try:
                    planned = self._limit(generate_search_query_plan(db, task_id, supplier))
                    return planned if planned else self.template_plan(supplier)
                except Exception:
                    return self.template_plan(supplier)
        return self.template_plan(supplier)

    def template_plan(self, supplier: dict[str, Any]) -> list[dict[str, str]]:
        company = supplier.get("company_name") or supplier.get("name") or "供应商"
        queries = [
            {"query": f"{company} 行政处罚 失信 被执行人 经营异常", "purpose": "risk_compliance"},
            {"query": f"{company} 诉讼 合同纠纷 付款纠纷 质量问题", "purpose": "risk_dispute"},
            {"query": f"{company} 破产 出口管制 严重违法 欠税", "purpose": "risk_financial_compliance"},
            {"query": f"{company} 官网 统一社会信用代码 注册资本 成立时间", "purpose": "company_profile"},
            {"query": f"{company} 企业信息 注册地址 经营范围 企业简介", "purpose": "company_profile"},
        ]
        return self._limit(queries)

    def _limit(self, queries: list[dict[str, str]]) -> list[dict[str, str]]:
        seen: set[str] = set()
        result: list[dict[str, str]] = []
        max_queries = 5
        for item in queries:
            query = str(item.get("query") or "").strip()
            if not query or query in seen:
                continue
            seen.add(query)
            result.append({"query": query, "purpose": str(item.get("purpose") or "due_diligence")})
            if len(result) >= max_queries:
                break
        return result


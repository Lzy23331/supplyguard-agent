from app.agents.base import AgentContext, BaseAgent
from app.evidence_providers.base import EvidenceCandidate
from app.evidence_providers.provider_manager import EvidenceProviderManager
from app.repositories import list_web_search_results
from app.tools.evidence_store import EvidenceStoreTool


class ExternalEvidenceAgent(BaseAgent):
    name = "EvidenceProviderManager"

    def __init__(self) -> None:
        self.manager = EvidenceProviderManager()
        self.store_tool = EvidenceStoreTool()

    def run(self, context: AgentContext) -> AgentContext:
        provider_names = [provider.name for provider in self.manager.providers]
        self.started(context, f"开始调用外部证据源：{'、'.join(provider_names)}。")
        self.event(
            context["task_id"],
            "provider_plan",
            "completed",
            f"本次任务已加载 Provider：{'、'.join(provider_names)}。",
            tool_name="EvidenceProviderManager",
            tool_input={"supplier_name": context["supplier"].get("name")},
            tool_output_summary="、".join(provider_names),
        )
        evidence = self.manager.collect(context["task_id"], context["supplier"])
        web_rows = list_web_search_results(context["task_id"])
        is_company_query = context["supplier"].get("query_type") == "company_name" or context["supplier"].get("company_name")
        if is_company_query and not any(item.get("source_type") == "web_search" for item in evidence) and not web_rows:
            fallback_item = EvidenceCandidate(
                title="联网搜索未发现明确高风险线索",
                content="腾讯云联网搜索未形成可评分的高风险证据；可能是 API 调用失败、返回为空或搜索结果与目标企业不够相关，需人工复核。",
                risk_keywords=["无明显风险"],
                source_type="web_search",
                source_name="腾讯云联网搜索",
                source_url=None,
                confidence=0.35,
                raw_text="联网搜索未发现明确高风险线索",
                severity="info",
                metadata={"should_use_for_scoring": False, "fallback_summary": True},
            ).model_dump()
            evidence.append(fallback_item)
            self.event(
                context["task_id"],
                "web_search_summary",
                "completed",
                "未获得可评分 web_search 证据且没有搜索记录，已写入联网搜索未发现明确高风险线索摘要。",
                tool_name="TencentWebSearchProvider",
                tool_input={"supplier_name": context["supplier"].get("name")},
                tool_output_summary="web_search_summary_count=1",
            )
        self.store_tool.save_many(context["task_id"], evidence)
        context["evidence"] = [*context.get("evidence", []), *evidence]
        context["evidence_items"] = [*context.get("evidence_items", []), *evidence]
        self.tool_called(
            context,
            self.store_tool.name,
            {"task_id": context["task_id"], "evidence_count": len(evidence)},
            f"已写入 {len(evidence)} 条外部/内部证据。",
        )
        self.completed(context, f"外部证据抽象层收集完成，共获得 {len(evidence)} 条可评分证据。")
        return context

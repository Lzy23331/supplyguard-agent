from app.agents.base import AgentContext, BaseAgent
from app.services.search_query_planner_service import SearchQueryPlannerService


class SearchQueryPlannerAgent(BaseAgent):
    name = "SearchQueryPlannerAgent"

    def __init__(self) -> None:
        self.service = SearchQueryPlannerService()

    def run(self, context: AgentContext) -> AgentContext:
        self.started(context, "开始生成企业尽调联网搜索计划。")
        queries = self.service.plan(context["task_id"], context["supplier"])
        context["search_queries"] = queries
        context["supplier"]["search_queries"] = queries
        self.event(
            context["task_id"],
            "search_query_plan",
            "completed",
            f"已生成 {len(queries)} 条联网搜索 query。",
            tool_name="SearchQueryPlannerService",
            tool_input={
                "supplier_name": context["supplier"].get("name"),
                "query_count": len(queries),
                "queries": queries,
                "fallback": False,
            },
            tool_output_summary="\n".join(f"{index}. {item.get('query')}" for index, item in enumerate(queries, start=1)),
        )
        self.completed(context, "联网搜索计划生成完成。")
        return context

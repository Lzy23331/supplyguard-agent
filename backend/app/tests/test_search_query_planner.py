from app.services.search_query_planner_service import SearchQueryPlannerService


def test_search_query_planner_templates_include_company_name(monkeypatch):
    monkeypatch.setenv("LLM_QUERY_PLANNER_ENABLED", "false")
    monkeypatch.setenv("TENCENT_WEB_SEARCH_MAX_QUERIES", "2")
    from app.config import get_settings

    get_settings.cache_clear()
    supplier = {
        "name": "某某科技有限公司",
        "industry": "电子元器件贸易",
        "region": "境内",
        "procurement_amount": 5000000,
        "cooperation_type": "紧急采购",
    }

    queries = SearchQueryPlannerService().plan("task_for_plan_test", supplier)

    assert 5 <= len(queries) <= 8
    assert all("某某科技有限公司" in item["query"] for item in queries)
    assert len({item["query"] for item in queries}) == len(queries)

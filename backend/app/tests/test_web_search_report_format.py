from app.tools.report_export import ReportExportTool


def test_report_shows_web_search_results_even_without_scoring_evidence():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "小米通讯科技有限公司", "company_name": "小米通讯科技有限公司", "query_type": "company_name"},
        evidence=[],
        web_search_results=[
            {
                "query": "小米通讯科技有限公司 企业简介",
                "title": "小米通讯科技有限公司企业简介",
                "url": "https://example.com/xiaomi-profile",
                "snippet": "公开网页摘要显示该公司主营通讯技术相关业务，未发现明显风险。",
                "decision": "display_only",
                "decision_reason": "目标相关但未形成可评分高风险证据",
                "matched_risk_keywords": [],
                "entity_match_score": 0.9,
                "domain_trust_score": 0.5,
                "metadata_json": {"provider_mode": "real"},
            }
        ],
        risk={"risk_level": "medium", "total_score": 50, "raw_score": 50, "recommendation": "建议补充材料后复核。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "联网搜索覆盖情况" in markdown
    assert "可评分风险证据" in markdown
    assert "联网搜索普通记录" in markdown
    assert "被排除结果摘要" in markdown
    assert "未形成可评分高风险证据" in markdown
    assert "https://example.com/xiaomi-profile" in markdown
    assert "真实企业名称查询任务（使用腾讯云联网搜索真实公开网页结果）" in markdown


def test_report_shows_scoring_web_search_reason_and_url():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[],
        web_search_results=[
            {
                "query": "比亚迪股份有限公司 行政处罚",
                "title": "比亚迪股份有限公司行政处罚信息",
                "url": "https://creditchina.gov.cn/byd-penalty",
                "snippet": "公开网页摘要显示比亚迪股份有限公司存在行政处罚记录。",
                "decision": "score_evidence",
                "decision_reason": "主体匹配、风险相关性和来源可信度均达到评分阈值",
                "matched_risk_keywords": ["administrative_penalty"],
                "entity_match_score": 0.9,
                "domain_trust_score": 0.95,
                "metadata_json": {"provider_mode": "real"},
            }
        ],
        risk={"risk_level": "high", "total_score": 80, "raw_score": 80, "recommendation": "建议人工复核。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "来源：腾讯云联网搜索" in markdown
    assert "https://creditchina.gov.cn/byd-penalty" in markdown
    assert "administrative_penalty" in markdown
    assert "主体匹配度：0.90" in markdown
    assert "来源可信度：0.95" in markdown
from app.tools.report_export import ReportExportTool


def test_report_shows_company_profile_section_with_source_url():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[],
        web_search_results=[],
        company_profile=[
            {
                "field_name": "industry",
                "field_value": "汽车制造 / 新能源汽车",
                "confidence": 0.72,
                "source_url": "https://www.byd.com/cn/about.html",
                "reason": "摘要包含行业关键词",
            }
        ],
        risk={"risk_level": "low", "total_score": 20, "raw_score": 20, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "企业基础信息补全" in markdown
    assert "汽车制造 / 新能源汽车" in markdown
    assert "https://www.byd.com/cn/about.html" in markdown
    assert "不等同官方工商核验" in markdown
from app.tools.report_export import ReportExportTool


def test_report_uses_query_plan_when_web_rows_have_no_query():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[],
        web_search_results=[
            {
                "title": "比亚迪股份有限公司企业简介",
                "url": "https://www.byd.com/cn/about.html",
                "snippet": "比亚迪股份有限公司企业介绍。",
                "decision": "display_only",
                "decision_reason": "目标相关但未形成可评分高风险证据",
                "entity_match_score": 0.9,
                "domain_trust_score": 0.7,
                "matched_risk_keywords": [],
                "metadata_json": {"provider_mode": "real", "should_use_for_scoring": False},
            }
        ],
        search_queries=[{"query": "比亚迪股份有限公司 官网 注册资本", "purpose": "company_profile"}],
        company_profile=[],
        risk={"risk_level": "low", "total_score": 26, "raw_score": 26, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "搜索 query 数：1" in markdown
    assert "https://www.byd.com/cn/about.html" in markdown
    assert "URL：未提供" not in markdown


def test_report_does_not_treat_no_risk_summary_as_scoring_evidence():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[
            {
                "source_type": "web_search",
                "title": "联网搜索未发现明确高风险线索",
                "content": "联网搜索未发现明确高风险线索。",
                "source_url": None,
                "risk_keywords": ["观察性风险"],
                "confidence": 0.35,
                "should_use_for_scoring": True,
                "severity": "info",
                "metadata_json": {"should_use_for_scoring": True},
            }
        ],
        web_search_results=[],
        search_queries=[{"query": "比亚迪股份有限公司 行政处罚", "purpose": "risk"}],
        company_profile=[],
        risk={"risk_level": "low", "total_score": 26, "raw_score": 26, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "联网搜索可评分风险证据：0 条" in markdown
    assert "未发现可评分的明确风险证据" in markdown
    scoring_section = markdown.split("### 可评分风险证据", 1)[1].split("### 联网搜索普通记录", 1)[0]
    assert "联网搜索未发现明确高风险线索" not in scoring_section


def test_report_profile_section_shows_missing_reasons():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[],
        web_search_results=[],
        search_queries=[{"query": "比亚迪股份有限公司 企业信息", "purpose": "company_profile"}],
        company_profile=[
            {"field_name": "company_full_name", "field_value": "比亚迪股份有限公司", "confidence": 0.75, "source_url": "https://www.byd.com", "reason": "搜索结果命中完整企业名称"},
            {"field_name": "registered_capital", "field_value": None, "confidence": 0.0, "source_url": "https://www.byd.com", "reason": "未能从联网搜索标题、摘要、URL 或 query 中可靠抽取该字段"},
        ],
        risk={"risk_level": "low", "total_score": 26, "raw_score": 26, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    assert "企业基础信息补全" in markdown
    assert "比亚迪股份有限公司" in markdown
    assert "未能从联网搜索标题" in markdown


def test_report_lists_multiple_real_web_search_records_before_summary_evidence():
    rows = [
        {
            "query": f"比亚迪股份有限公司 查询 {index}",
            "rank": index,
            "title": f"比亚迪股份有限公司搜索结果{index}",
            "url": f"https://example.com/byd-{index}",
            "snippet": "公开网页摘要，未形成可评分高风险证据。",
            "decision": "display_only",
            "decision_reason": "目标相关但未形成可评分高风险证据",
            "matched_risk_keywords": [],
            "entity_match_score": 0.85,
            "domain_trust_score": 0.60,
            "metadata_json": {"provider_mode": "real", "should_use_for_scoring": False},
        }
        for index in range(1, 5)
    ]
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[
            {
                "source_type": "web_search",
                "title": "联网搜索未发现明确高风险线索",
                "content": "联网搜索未发现明确高风险线索。",
                "source_url": None,
                "risk_keywords": ["无明显风险"],
                "confidence": 0.35,
                "should_use_for_scoring": True,
                "metadata_json": {"should_use_for_scoring": True},
            }
        ],
        web_search_results=rows,
        search_queries=[{"query": "比亚迪股份有限公司 官网", "purpose": "company_profile"}],
        company_profile=[],
        risk={"risk_level": "low", "total_score": 26, "raw_score": 26, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    ordinary_section = markdown.split("### 联网搜索普通记录", 1)[1].split("### 被排除结果摘要", 1)[0]
    assert ordinary_section.count("https://example.com/byd-") >= 3
    assert "URL：未提供" not in markdown
    assert "query：比亚迪股份有限公司 查询 1" in markdown
    assert "是否参与评分：否" in ordinary_section


def test_report_all_evidence_marks_no_obvious_risk_as_not_scoring_even_if_flag_true():
    markdown = ReportExportTool().build_markdown(
        supplier={"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name"},
        evidence=[
            {
                "source_type": "web_search",
                "title": "联网搜索未发现明确高风险线索",
                "content": "联网搜索未发现明确高风险线索。",
                "source_url": None,
                "risk_keywords": ["无明显风险"],
                "confidence": 0.35,
                "should_use_for_scoring": True,
                "metadata_json": {"should_use_for_scoring": True},
            }
        ],
        web_search_results=[],
        company_profile=[],
        risk={"risk_level": "low", "total_score": 26, "raw_score": 26, "recommendation": "建议准入。", "dimensions": [], "triggered_rules": []},
        policies=[],
    )

    evidence_section = markdown.split("### 全部任务证据（含不参与评分）", 1)[1].split("说明：", 1)[0]
    assert "是否参与评分：否" in evidence_section
    assert "是否参与评分：是" not in evidence_section

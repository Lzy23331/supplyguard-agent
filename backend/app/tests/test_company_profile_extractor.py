from app.services.company_profile_extractor import CompanyProfileExtractor


def test_company_profile_extractor_reads_fields_from_search_snippets():
    rows = [
        {
            "title": "比亚迪股份有限公司企业信息 官网",
            "snippet": "比亚迪股份有限公司 注册资本 291114万元 成立日期 1995-02-10 注册地址 广东省深圳市 经营状态 存续，主营新能源汽车和汽车业务。",
            "url": "https://www.byd.com/cn/about.html",
            "query": "比亚迪股份有限公司 官网 统一社会信用代码 注册资本 成立时间",
            "decision": "display_only",
            "entity_match_score": 0.9,
            "domain_trust_score": 0.7,
            "rank": 1,
        }
    ]

    fields = CompanyProfileExtractor().extract(task_id="task-1", company_name="比亚迪股份有限公司", search_results=rows)
    by_name = {item["field_name"]: item for item in fields}

    assert by_name["company_full_name"]["field_value"] == "比亚迪股份有限公司"
    assert by_name["registered_capital"]["field_value"].startswith("291114")
    assert by_name["region"]["field_value"] == "广东省"
    assert by_name["industry"]["field_value"] == "汽车制造 / 新能源汽车"
    assert by_name["website"]["source_url"] == "https://www.byd.com/cn/about.html"
    assert all(item["requires_manual_verification"] for item in fields)

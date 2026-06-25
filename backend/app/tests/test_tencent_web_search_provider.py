from app.evidence_providers.tencent_web_search_provider import TencentWebSearchProvider
from app.tools.search_result_evidence_extractor import SearchResultEvidenceExtractor


def test_tencent_web_search_standardizes_fake_response():
    provider = TencentWebSearchProvider()
    data = {
        "Response": {
            "Results": [
                {
                    "Title": "某某科技有限公司行政处罚信息",
                    "Snippet": "公开网页摘要显示该企业存在行政处罚记录。",
                    "Url": "https://example.com/a",
                    "Site": "example.com",
                }
            ]
        }
    }

    results = provider.standardize_response(data, query="某某科技有限公司 行政处罚", purpose="business_risk", top_k=5)

    assert results[0]["query"] == "某某科技有限公司 行政处罚"
    assert results[0]["purpose"] == "business_risk"
    assert results[0]["title"] == "某某科技有限公司行政处罚信息"
    assert results[0]["url"] == "https://example.com/a"
    assert results[0]["snippet"] == "公开网页摘要显示该企业存在行政处罚记录。"
    assert results[0]["site"] == "example.com"
    assert results[0]["source"] == "tencent_web_search"
    assert results[0]["rank"] == 1
    assert results[0]["provider_mode"] == "real"
    assert results[0]["retrieved_at"]


def test_search_result_evidence_extractor_marks_strong_web_search_evidence():
    evidence = SearchResultEvidenceExtractor().extract([
        {
            "query": "某某科技有限公司 失信 黑名单",
            "purpose": "compliance_risk",
            "title": "某某科技有限公司被执行人信息",
            "snippet": "摘要包含失信、被执行人和黑名单风险提示。",
            "url": "https://example.com/risk",
            "rank": 1,
        }
    ])

    assert evidence
    item = evidence[0].model_dump()
    assert item["source_type"] == "web_search"
    assert item["source_name"] == "腾讯云联网搜索"
    assert item["confidence"] >= 0.65
    assert item["metadata"]["should_use_for_scoring"] is True


def test_search_result_evidence_requires_exact_company_match_for_scoring():
    evidence = SearchResultEvidenceExtractor().extract([
        {
            "query": "小米通讯科技有限公司 经营异常",
            "purpose": "business_risk",
            "company_name": "小米通讯科技有限公司",
            "title": "小米数字科技有限公司被列入经营异常",
            "snippet": "摘要包含经营异常，但主体是另一家小米关联企业。",
            "url": "https://example.com/xiaomi-digital",
            "rank": 1,
        }
    ])

    item = evidence[0].model_dump()
    assert item["source_type"] == "web_search"
    assert item["confidence"] < 0.5
    assert item["metadata"]["exact_company_match"] is False
    assert item["metadata"]["should_use_for_scoring"] is False


def test_search_result_without_risk_keywords_still_writes_no_obvious_risk_evidence():
    evidence = SearchResultEvidenceExtractor().extract([
        {
            "query": "小米通讯科技有限公司 注册资本",
            "purpose": "company_profile",
            "company_name": "小米通讯科技有限公司",
            "title": "小米通讯科技有限公司企业介绍",
            "snippet": "公开网页摘要显示该公司主营通讯技术相关业务。",
            "url": "https://example.com/xiaomi-profile",
            "rank": 1,
        }
    ])

    item = evidence[0].model_dump()
    assert item["source_type"] == "web_search"
    assert item["risk_keywords"] == ["search_observation"]
    assert item["source_url"] == "https://example.com/xiaomi-profile"
    assert item["metadata"]["should_use_for_scoring"] is False

from app.services.search_evidence_quality_evaluator import SearchEvidenceQualityEvaluator


def evaluate(row, company_name="比亚迪股份有限公司"):
    return SearchEvidenceQualityEvaluator().evaluate_one(row, company_name=company_name)


def test_exact_target_administrative_penalty_scores():
    row = {
        "title": "比亚迪股份有限公司行政处罚决定书",
        "url": "https://creditchina.gov.cn/xinyongfuwu/xzcf/123.html",
        "snippet": "比亚迪股份有限公司因相关事项受到行政处罚。",
        "rank": 1,
    }

    result = evaluate(row)

    assert result["decision"] == "score_evidence"
    assert "administrative_penalty" in result["matched_risk_keywords"]
    assert result["metadata_json"]["should_use_for_scoring"] is True


def test_profile_or_intro_is_display_only():
    row = {
        "title": "比亚迪股份有限公司企业简介",
        "url": "https://www.byd.com/cn/about.html",
        "snippet": "比亚迪股份有限公司是一家高新技术企业。",
        "rank": 1,
    }

    result = evaluate(row)

    assert result["decision"] == "display_only"
    assert result["metadata_json"]["should_use_for_scoring"] is False


def test_dealer_and_brand_news_do_not_score():
    dealer = evaluate({"title": "比亚迪4S店销售服务中心投诉", "url": "https://news.qq.com/a.html", "snippet": "某地经销商服务投诉。"})
    brand = evaluate({"title": "比亚迪新车发布销量新闻", "url": "https://news.qq.com/b.html", "snippet": "车型发布和销量表现。"})

    assert dealer["decision"] in {"display_only", "exclude"}
    assert brand["decision"] in {"display_only", "exclude"}


def test_unrelated_same_name_excluded():
    result = evaluate({"title": "深圳某餐饮公司合同纠纷", "url": "https://court.gov.cn/a.html", "snippet": "该公司合同纠纷信息。"})

    assert result["decision"] == "exclude"
    assert result["excluded_reason"] == "entity_unrelated"


def test_no_obvious_risk_never_scores():
    result = evaluate({"title": "比亚迪股份有限公司官网", "url": "https://www.byd.com", "snippet": "未发现明显风险。"})

    assert result["decision"] == "display_only"
    assert result["metadata_json"]["should_use_for_scoring"] is False

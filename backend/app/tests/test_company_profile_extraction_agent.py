from app.agents.company_profile_extraction_agent import CompanyProfileExtractionAgent
from app.database import init_db
from app.repositories import create_task_record, list_company_profile_snapshots, save_web_search_results
from app.schemas import SupplierCreate
from app.tools.risk_rules import RiskRuleTool


def test_company_profile_agent_persists_and_completes_supplier_fields():
    init_db()
    task_id = create_task_record(SupplierCreate(name="比亚迪股份有限公司"), query_type="company_name", company_name="比亚迪股份有限公司")
    save_web_search_results(
        task_id,
        [
            {
                "query": "比亚迪股份有限公司 企业信息 注册地址 经营范围 企业简介",
                "title": "比亚迪股份有限公司企业信息",
                "url": "https://www.byd.com/cn/about.html",
                "snippet": "比亚迪股份有限公司 注册地址 广东省深圳市，经营状态 存续，主营新能源汽车。",
                "rank": 1,
                "decision": "display_only",
                "entity_match_score": 0.9,
                "domain_trust_score": 0.7,
                "matched_risk_keywords": [],
                "metadata_json": {"provider_mode": "real"},
            }
        ],
    )
    context = {"task_id": task_id, "supplier": {"name": "比亚迪股份有限公司", "company_name": "比亚迪股份有限公司", "query_type": "company_name", "procurement_amount": 500000}}

    result = CompanyProfileExtractionAgent().run(context)

    snapshots = list_company_profile_snapshots(task_id)
    assert snapshots
    assert result["supplier"]["industry"] == "汽车制造 / 新能源汽车"
    assert result["supplier"]["region"] == "广东省"


def test_profile_completed_fields_reduce_missing_rule_penalties():
    supplier_without_profile = {"name": "比亚迪股份有限公司", "procurement_amount": 500000}
    supplier_with_profile = {"name": "比亚迪股份有限公司", "website": "https://www.byd.com", "industry": "汽车制造 / 新能源汽车", "region": "广东省", "procurement_amount": 500000}

    no_profile = RiskRuleTool().assess([], supplier_without_profile)
    with_profile = RiskRuleTool().assess([], supplier_with_profile)

    assert with_profile["raw_score"] < no_profile["raw_score"]

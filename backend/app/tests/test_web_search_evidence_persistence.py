from app.database import init_db
from app.evidence_providers.tencent_web_search_provider import TencentWebSearchProvider
from app.repositories import create_task_record, list_evidence, list_web_search_results
from app.schemas import SupplierCreate
from app.tools.evidence_store import EvidenceStoreTool
from app.tools.external_evidence_normalizer import ExternalEvidenceNormalizer


class FakeTencentWebSearchProvider(TencentWebSearchProvider):
    def is_configured(self) -> bool:
        return True

    def _request(self, payload):
        return {
            "Response": {
                "Query": payload["Query"],
                "Pages": [
                    {
                        "title": "比亚迪股份有限公司行政处罚信息",
                        "passage": "公开网页摘要显示比亚迪股份有限公司存在行政处罚记录。",
                        "url": "https://creditchina.gov.cn/byd-penalty",
                        "site": "creditchina.gov.cn",
                    },
                    {
                        "title": "比亚迪股份有限公司企业简介",
                        "passage": "公开网页摘要显示该企业主营汽车业务，未发现明显风险。",
                        "url": "https://www.byd.com/profile",
                        "site": "byd.com",
                    },
                ],
            }
        }


def test_fake_tencent_provider_persists_web_search_results_and_scoring_evidence():
    init_db()
    task_id = create_task_record(SupplierCreate(name="比亚迪股份有限公司"), query_type="company_name", company_name="比亚迪股份有限公司")
    provider = FakeTencentWebSearchProvider()
    candidates = provider.collect(
        company_name="比亚迪股份有限公司",
        resolved_company={"name": "比亚迪股份有限公司", "search_queries": [{"query": "比亚迪股份有限公司 行政处罚", "purpose": "business_risk"}]},
        context={"task_id": task_id},
    )
    evidence = [ExternalEvidenceNormalizer().normalize(candidate, provider.name, provider.source_type) for candidate in candidates]
    EvidenceStoreTool().save_many(task_id, evidence)

    web_rows = list_web_search_results(task_id)
    stored = list_evidence(task_id)
    assert len(web_rows) == 2
    assert any(row["decision"] == "score_evidence" for row in web_rows)
    assert any(row["decision"] == "display_only" for row in web_rows)
    assert stored
    assert stored[0]["source_type"] == "web_search"
    assert stored[0]["source_name"] == "腾讯云联网搜索"
    assert stored[0]["source_url"] == "https://creditchina.gov.cn/byd-penalty"
    assert stored[0]["should_use_for_scoring"] == 1

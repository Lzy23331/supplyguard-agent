from app.evidence_providers.base import EvidenceCandidate
from app.evidence_providers.provider_manager import EvidenceProviderManager
from app.evidence_providers.real_news_search_provider import RealNewsSearchProvider
from app.database import init_db


class StaticRealProvider(RealNewsSearchProvider):
    name = "StaticRealProvider"
    provider_name = "StaticRealProvider"
    source_type = "real_external"

    def is_configured(self) -> bool:
        return True

    def collect(self, *, company_name, resolved_company=None, context=None):
        return [
            EvidenceCandidate(
                title="真实 Provider 骨架测试证据",
                content=f"{company_name} 存在合同纠纷测试信号。",
                risk_keywords=["合同纠纷"],
                source_type=self.source_type,
                source_name=self.name,
                confidence=0.8,
                severity="warning",
            )
        ]


def test_provider_manager_normalizes_evidence_candidate():
    init_db()
    manager = EvidenceProviderManager(providers=[StaticRealProvider()])
    evidence = manager.collect("task_without_db_for_static_provider", {"name": "Demo Supplier"})

    assert evidence[0]["source_type"] == "real_external"
    assert evidence[0]["source_name"] == "StaticRealProvider"
    assert evidence[0]["title"]
    assert evidence[0]["content"]

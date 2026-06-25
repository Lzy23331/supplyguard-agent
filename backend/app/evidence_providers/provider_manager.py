from typing import Any

from app.config import get_settings
from app.evidence_providers.base import EvidenceProvider
from app.evidence_providers.internal_record_csv_provider import InternalRecordCsvProvider
from app.evidence_providers.mock_company_info_provider import MockCompanyInfoProvider
from app.evidence_providers.mock_news_provider import MockNewsProvider
from app.evidence_providers.mock_sanctions_provider import MockSanctionsProvider
from app.evidence_providers.real_company_info_provider import RealCompanyInfoProvider
from app.evidence_providers.real_news_search_provider import RealNewsSearchProvider
from app.evidence_providers.real_sanctions_provider import RealSanctionsProvider
from app.evidence_providers.real_web_search_provider import RealWebSearchProvider
from app.evidence_providers.tencent_web_search_provider import TencentWebSearchProvider
from app.services.provider_audit_service import ProviderAuditService
from app.tools.external_evidence_normalizer import ExternalEvidenceNormalizer


class EvidenceProviderManager:
    name = "EvidenceProviderManager"

    def __init__(self, providers: list[EvidenceProvider] | None = None) -> None:
        self.settings = get_settings()
        self.audit = ProviderAuditService()
        self.providers = providers or self._configured_providers()
        self.normalizer = ExternalEvidenceNormalizer()
        self.fallbacks = {
            "RealCompanyInfoProvider": MockCompanyInfoProvider(),
            "RealWebSearchProvider": MockNewsProvider(),
            "TencentWebSearchProvider": MockNewsProvider(),
            "RealNewsSearchProvider": MockNewsProvider(),
            "RealSanctionsProvider": MockSanctionsProvider(),
        }

    def _configured_providers(self) -> list[EvidenceProvider]:
        if self.settings.provider_mode == "disabled":
            return [InternalRecordCsvProvider()]
        if self.settings.provider_mode == "mock" and self.settings.web_search_provider != "real":
            return [MockCompanyInfoProvider(), MockNewsProvider(), MockSanctionsProvider(), InternalRecordCsvProvider()]

        providers: list[EvidenceProvider] = []
        if self.settings.company_info_provider != "disabled":
            providers.append(RealCompanyInfoProvider() if self.settings.company_info_provider == "real" or self.settings.provider_mode == "real" else MockCompanyInfoProvider())
        if self.settings.web_search_provider != "disabled":
            if self.settings.web_search_provider == "real" or self.settings.provider_mode == "real":
                providers.append(TencentWebSearchProvider() if self.settings.web_search_api == "tencent" else RealWebSearchProvider())
            else:
                providers.append(MockNewsProvider())
        providers.append(RealNewsSearchProvider())
        if self.settings.sanctions_provider != "disabled":
            providers.append(RealSanctionsProvider() if self.settings.sanctions_provider == "real" or self.settings.provider_mode == "real" else MockSanctionsProvider())
        providers.append(InternalRecordCsvProvider())
        return providers

    def collect(self, task_id: str, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        for provider_index, provider in enumerate(self.providers):
            provider_name = getattr(provider, "provider_name", provider.name)
            self.audit.event(
                task_id,
                "provider_started",
                "running",
                f"{provider_name} 开始收集证据。",
                provider_name,
                {"supplier_name": supplier.get("name")},
            )
            try:
                if not provider.is_configured():
                    fallback = self.fallbacks.get(provider_name)
                    if fallback and self.settings.provider_fallback_to_mock:
                        self.audit.event(
                            task_id,
                            "provider_warning",
                            "warning",
                            f"{provider_name} 未配置 API Key，已回退 {fallback.name}。",
                            provider_name,
                            {"supplier_name": supplier.get("name")},
                            "fallback_to_mock",
                        )
                        provider = fallback
                        provider_name = provider.name
                    else:
                        self.audit.event(
                            task_id,
                            "provider_warning",
                            "warning",
                            f"{provider_name} 未配置 API Key，已跳过该 Provider。",
                            provider_name,
                            {"supplier_name": supplier.get("name")},
                            "skipped_not_configured",
                        )
                        continue
                candidates = provider.collect(
                    company_name=supplier.get("name") or supplier.get("company_name") or "",
                    resolved_company=supplier,
                    context={"task_id": task_id, "search_queries": supplier.get("search_queries") or []},
                )
                normalized = []
                for candidate_index, candidate in enumerate(candidates):
                    if hasattr(candidate, "model_dump"):
                        candidate = candidate.model_dump()
                    candidate = dict(candidate)
                    if candidate.get("id"):
                        candidate["id"] = f"{provider_index}:{candidate_index}:{candidate['id']}"
                    normalized.append(self.normalizer.normalize(candidate, provider_name, provider.source_type))
                evidence.extend(normalized)
                self.audit.event(
                    task_id,
                    "provider_completed",
                    "completed",
                    f"{provider_name} 返回 {len(normalized)} 条标准化证据。",
                    provider_name,
                    {"supplier_name": supplier.get("name")},
                    f"evidence_count={len(normalized)}",
                )
            except Exception as exc:
                fallback = self.fallbacks.get(provider_name)
                if fallback and self.settings.provider_fallback_to_mock:
                    self.audit.event(
                        task_id,
                        "provider_warning",
                        "warning",
                        f"{provider_name} 调用失败，已回退 {fallback.name}：{exc}",
                        provider_name,
                        {"supplier_name": supplier.get("name")},
                        "fallback_to_mock",
                    )
                    candidates = fallback.collect(company_name=supplier.get("name") or "", resolved_company=supplier, context={"task_id": task_id, "search_queries": supplier.get("search_queries") or []})
                    normalized = []
                    for candidate_index, candidate in enumerate(candidates):
                        if hasattr(candidate, "model_dump"):
                            candidate = candidate.model_dump()
                        candidate = dict(candidate)
                        if candidate.get("id"):
                            candidate["id"] = f"{provider_index}:fallback:{candidate_index}:{candidate['id']}"
                        normalized.append(self.normalizer.normalize(candidate, fallback.name, fallback.source_type))
                    evidence.extend(normalized)
                    self.audit.event(
                        task_id,
                        "provider_completed",
                        "completed",
                        f"{fallback.name} fallback 返回 {len(normalized)} 条标准化证据。",
                        fallback.name,
                        {"supplier_name": supplier.get("name")},
                        f"evidence_count={len(normalized)}",
                    )
                else:
                    self.audit.event(
                        task_id,
                        "provider_warning",
                        "warning",
                        f"{provider_name} 调用失败，已跳过该外部证据源：{exc}",
                        provider_name,
                        {"supplier_name": supplier.get("name")},
                        str(exc),
                    )
        return evidence

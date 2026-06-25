from typing import Any

import httpx

from app.config import get_settings
from app.evidence_providers.base import EvidenceCandidate, EvidenceProvider


class RealCompanyInfoProvider(EvidenceProvider):
    name = "RealCompanyInfoProvider"
    provider_name = "RealCompanyInfoProvider"
    source_type = "real_external"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        return bool(
            self.settings.opencorporates_api_token
            or self.settings.companies_house_api_key
            or self.settings.qcc_api_key
            or self.settings.tianyancha_token
        )

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[EvidenceCandidate]:
        if self.settings.opencorporates_api_token:
            return self._collect_opencorporates(company_name)
        if self.settings.companies_house_api_key:
            return self._collect_companies_house(company_name)
        return []

    def _collect_opencorporates(self, company_name: str) -> list[EvidenceCandidate]:
        params = {"q": company_name, "api_token": self.settings.opencorporates_api_token}
        with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
            data = client.get("https://api.opencorporates.com/v0.4/companies/search", params=params).json()
        companies = ((data.get("results") or {}).get("companies") or [])[:3]
        return [
            EvidenceCandidate(
                title="企业基础信息查询结果",
                content=f"OpenCorporates 返回企业：{(item.get('company') or {}).get('name') or company_name}。",
                risk_keywords=[],
                source_type=self.source_type,
                source_name=self.name,
                source_url=(item.get("company") or {}).get("opencorporates_url"),
                confidence=0.7,
                severity="info",
                metadata={"provider_api": "opencorporates"},
            )
            for item in companies
        ]

    def _collect_companies_house(self, company_name: str) -> list[EvidenceCandidate]:
        params = {"q": company_name, "items_per_page": 3}
        with httpx.Client(timeout=self.settings.provider_timeout_seconds, auth=(self.settings.companies_house_api_key or "", "")) as client:
            data = client.get("https://api.company-information.service.gov.uk/search/companies", params=params).json()
        return [
            EvidenceCandidate(
                title="Companies House 企业查询结果",
                content=f"Companies House 返回企业：{row.get('title') or company_name}。",
                risk_keywords=[],
                source_type=self.source_type,
                source_name=self.name,
                source_url=f"https://find-and-update.company-information.service.gov.uk/company/{row.get('company_number')}" if row.get("company_number") else None,
                confidence=0.7,
                severity="info",
                metadata={"provider_api": "companies_house", "company_status": row.get("company_status")},
            )
            for row in (data.get("items") or [])[:3]
        ]

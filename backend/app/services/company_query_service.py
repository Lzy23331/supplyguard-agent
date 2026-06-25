from typing import Any

from app.evidence_providers.mock_company_info_provider import MockCompanyInfoProvider
from app.schemas import SupplierCreate


class CompanyQueryService:
    def __init__(self) -> None:
        self.company_info = MockCompanyInfoProvider()

    def resolve_profile(
        self,
        company_name: str,
        procurement_amount: float | None = None,
        cooperation_type: str | None = None,
    ) -> dict[str, Any]:
        profile = self.company_info.resolve(company_name)
        if not profile:
            return {
                "name": company_name,
                "website": None,
                "industry": None,
                "region": None,
                "annual_spend": procurement_amount or 0,
                "procurement_amount": procurement_amount or 0,
                "cooperation_type": cooperation_type,
                "business_status": "待核验",
                "company_age_years": None,
                "profile_completeness": "低",
                "ownership_transparency": "低",
                "summary": "未在模拟企业信息库命中精确企业档案，按信息不完整主体进入尽调流程。",
                "tags": ["企业名查询", "未命中模拟档案"],
                "expected_risk_level": None,
                "resolution_status": "incomplete_created",
            }
        resolved = {
            key: profile.get(key)
            for key in [
                "name",
                "website",
                "industry",
                "region",
                "annual_spend",
                "business_status",
                "company_age_years",
                "profile_completeness",
                "ownership_transparency",
                "urgency",
                "summary",
                "tags",
                "expected_risk_level",
            ]
        }
        resolved["procurement_amount"] = procurement_amount if procurement_amount is not None else profile.get("annual_spend") or 0
        resolved["annual_spend"] = profile.get("annual_spend") or resolved["procurement_amount"] or 0
        resolved["cooperation_type"] = cooperation_type or profile.get("cooperation_type")
        resolved["resolution_status"] = "matched_mock_profile"
        return resolved

    def placeholder_payload(
        self,
        company_name: str,
        procurement_amount: float | None = None,
        cooperation_type: str | None = None,
    ) -> SupplierCreate:
        return SupplierCreate(
            name=company_name,
            annual_spend=procurement_amount or 0,
            procurement_amount=procurement_amount or 0,
            cooperation_type=cooperation_type,
            business_status="待解析",
            profile_completeness="低",
            ownership_transparency="低",
            summary="企业名查询任务占位资料，等待 CompanyResolverAgent 解析。",
            tags=["企业名查询"],
        )

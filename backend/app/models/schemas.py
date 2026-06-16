from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

RiskLevel = Literal["low", "medium", "high"]


class SupplierBase(BaseModel):
    id: str | None = None
    sample_key: str | None = None
    name: str
    website: str | None = None
    industry: str | None = None
    region: str | None = None
    annual_spend: float = Field(default=0, ge=0)
    procurement_amount: float | None = Field(default=None, ge=0)
    cooperation_type: str | None = None
    business_status: str | None = None
    company_age_years: int | None = Field(default=None, ge=0)
    profile_completeness: str | None = None
    ownership_transparency: str | None = None
    urgency: str | None = None
    summary: str | None = None
    tags: list[str] = []
    expected_risk_level: RiskLevel | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierRead(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: str | None = None


class EvidenceItem(BaseModel):
    id: str | None = None
    source: str
    category: str | None = None
    title: str
    content: str
    severity: str = "info"
    rule_signals: list[str] = []
    economic_rationale: str | None = None
    url: str | None = None


class PolicyChunk(BaseModel):
    doc_name: str
    section_title: str
    content: str
    keywords: list[str] = []
    score: int = 0
    matched_keywords: list[str] = []


class RiskRuleHit(BaseModel):
    rule_id: str
    dimension: str
    rule_name: str
    score: int
    reason: str
    evidence_ids: list[str] = []


class RiskAssessmentResult(BaseModel):
    raw_score: int
    total_score: int
    risk_level: RiskLevel
    dimension_scores: dict[str, int]
    triggered_rules: list[RiskRuleHit]
    recommendation: str

    @property
    def hit_rules(self) -> list[dict[str, Any]]:
        return [rule.model_dump() for rule in self.triggered_rules]

from typing import Any

from pydantic import BaseModel, Field


class EvidenceCandidate(BaseModel):
    title: str
    content: str
    risk_keywords: list[str] = Field(default_factory=list)
    source_type: str
    source_name: str
    source_url: str | None = None
    confidence: float = 0.7
    raw_text: str | None = None
    severity: str = "info"
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceProvider:
    name = "EvidenceProvider"
    provider_name = "EvidenceProvider"
    source_type = "mock_external"

    def is_configured(self) -> bool:
        return True

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any] | EvidenceCandidate]:
        supplier = resolved_company or {"name": company_name}
        return self.search(supplier)

    def search(self, supplier: dict[str, Any]) -> list[dict[str, Any]]:
        return []

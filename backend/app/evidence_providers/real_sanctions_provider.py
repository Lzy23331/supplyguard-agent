import csv
from pathlib import Path
from typing import Any

import httpx

from app.config import get_settings
from app.evidence_providers.base import EvidenceCandidate, EvidenceProvider


class RealSanctionsProvider(EvidenceProvider):
    name = "RealSanctionsProvider"
    provider_name = "RealSanctionsProvider"
    source_type = "real_external"

    def __init__(self) -> None:
        self.settings = get_settings()

    def is_configured(self) -> bool:
        local_csv = self._local_csv()
        return bool(self.settings.opensanctions_api_key or local_csv.exists())

    def collect(
        self,
        *,
        company_name: str,
        resolved_company: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[EvidenceCandidate]:
        if self.settings.opensanctions_api_key:
            return self._collect_opensanctions(company_name)
        return self._collect_local_csv(company_name)

    def _collect_opensanctions(self, company_name: str) -> list[EvidenceCandidate]:
        headers = {"Authorization": f"ApiKey {self.settings.opensanctions_api_key}"}
        payload = {"queries": {"q0": {"schema": "Organization", "properties": {"name": [company_name]}}}}
        with httpx.Client(timeout=self.settings.provider_timeout_seconds) as client:
            data = client.post("https://api.opensanctions.org/match/default", json=payload, headers=headers).json()
        responses = ((data.get("responses") or {}).get("q0") or {}).get("results") or []
        candidates = []
        for row in responses[:5]:
            score = float(row.get("score") or 0)
            if score < 0.7:
                continue
            entity = row.get("properties") or {}
            name = (entity.get("name") or [company_name])[0]
            candidates.append(
                EvidenceCandidate(
                    title="制裁/名单筛查疑似命中",
                    content=f"OpenSanctions 返回相似实体：{name}，匹配分 {score:.2f}。",
                    risk_keywords=["制裁", "黑名单"],
                    source_type=self.source_type,
                    source_name=self.name,
                    confidence=min(score, 0.95),
                    severity="critical",
                    metadata={"match_score": score},
                )
            )
        return candidates

    def _collect_local_csv(self, company_name: str) -> list[EvidenceCandidate]:
        path = self._local_csv()
        if not path.exists():
            return []
        matches = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                listed_name = (row.get("name") or row.get("company_name") or "").strip()
                if listed_name.lower() != company_name.strip().lower():
                    continue
                matches.append(
                    EvidenceCandidate(
                        title=row.get("title") or "本地名单筛查命中",
                        content=row.get("content") or f"本地名单中存在同名实体：{listed_name}。",
                        risk_keywords=["制裁", "黑名单"],
                        source_type=self.source_type,
                        source_name=f"{self.name}:local_csv",
                        confidence=float(row.get("confidence") or 0.8),
                        severity=row.get("severity") or "critical",
                        metadata={"local_csv": str(path)},
                    )
                )
        return matches

    def _local_csv(self) -> Path:
        path = Path(self.settings.sanctions_local_csv)
        return path if path.is_absolute() else self.settings.project_root / path

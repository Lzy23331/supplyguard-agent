from typing import Any

from app.repositories import add_evidence


class EvidenceStoreTool:
    name = "EvidenceStoreTool"

    def save_many(self, task_id: str, evidence: list[dict[str, Any]]) -> int:
        for item in evidence:
            add_evidence(task_id, item)
        return len(evidence)


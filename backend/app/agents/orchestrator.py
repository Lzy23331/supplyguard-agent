from typing import Any

from app.agents.base import AgentContext
from app.agents.business_risk import BusinessRiskAgent
from app.agents.compliance_risk import ComplianceRiskAgent
from app.agents.evidence_collector import EvidenceCollectorAgent
from app.agents.intake import IntakeAgent
from app.agents.report import ReportAgent
from app.repositories import add_event, update_task


class Orchestrator:
    def __init__(self) -> None:
        self.agents = [
            IntakeAgent(),
            EvidenceCollectorAgent(),
            ComplianceRiskAgent(),
            BusinessRiskAgent(),
            ReportAgent(),
        ]

    def run(self, task_id: str, supplier: dict[str, Any]) -> dict[str, Any]:
        update_task(task_id, status="running")
        context = AgentContext(task_id=task_id, supplier=supplier)
        try:
            for agent in self.agents:
                add_event(task_id, agent.name, "running", f"{agent.name} 开始执行。", [])
                context = agent.run(context)
            risk = context["risk"]
            update_task(
                task_id,
                status="completed",
                risk_level=risk["risk_level"],
                total_score=risk["total_score"],
                recommendation=risk["recommendation"],
            )
            return context
        except Exception as exc:
            add_event(task_id, "Orchestrator", "failed", str(exc), [])
            update_task(task_id, status="failed")
            raise

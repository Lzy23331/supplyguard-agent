from app.agents.base import AgentContext
from app.agents.business_risk import BusinessRiskAgent
from app.agents.compliance_risk import ComplianceRiskAgent
from app.agents.company_resolver_agent import CompanyResolverAgent
from app.agents.company_profile_extraction_agent import CompanyProfileExtractionAgent
from app.agents.evidence_collector import EvidenceCollectorAgent
from app.agents.external_evidence_agent import ExternalEvidenceAgent
from app.agents.intake import IntakeAgent
from app.agents.material_analysis_agent import MaterialAnalysisAgent
from app.agents.report import ReportAgent
from app.agents.search_query_planner_agent import SearchQueryPlannerAgent
from app.repositories import add_event, update_task


class Orchestrator:
    name = "Orchestrator"

    def __init__(self) -> None:
        self.default_agents = [
            IntakeAgent(),
            EvidenceCollectorAgent(),
            MaterialAnalysisAgent(),
            ComplianceRiskAgent(),
            BusinessRiskAgent(),
            ReportAgent(),
        ]
        self.company_query_agents = [
            CompanyResolverAgent(),
            SearchQueryPlannerAgent(),
            IntakeAgent(),
            EvidenceCollectorAgent(),
            ExternalEvidenceAgent(),
            CompanyProfileExtractionAgent(),
            MaterialAnalysisAgent(),
            ComplianceRiskAgent(),
            BusinessRiskAgent(),
            ReportAgent(),
        ]

    def run(self, task_id: str, supplier: dict) -> AgentContext:
        context = AgentContext(task_id=task_id, supplier=supplier)
        add_event(task_id, self.name, "agent_started", "running", "编排器开始执行同步尽调流程。")
        update_task(task_id, status="running")
        try:
            agents = self.company_query_agents if supplier.get("query_type") == "company_name" or supplier.get("company_name") else self.default_agents
            for agent in agents:
                context = agent.run(context)
            risk = context["risk"]
            update_task(
                task_id,
                status="completed",
                risk_level=risk["risk_level"],
                total_score=risk["total_score"],
                recommendation=risk["recommendation"],
                summary=f"{supplier.get('name')} 尽调完成：{risk['risk_level']} / {risk['total_score']}",
            )
            add_event(task_id, self.name, "agent_completed", "completed", "编排器完成全部 Agent 流程。")
            return context
        except Exception as exc:
            update_task(task_id, status="failed", summary=str(exc))
            add_event(task_id, self.name, "agent_failed", "failed", f"编排器执行失败：{exc}")
            raise



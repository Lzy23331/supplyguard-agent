from app.agents.base import AgentContext
from app.agents.company_resolver_agent import CompanyResolverAgent
from app.database import init_db
from app.repositories import create_task_record, get_task, list_events
from app.services.company_query_service import CompanyQueryService


def test_company_resolver_agent_resolves_mock_profile():
    init_db()
    payload = CompanyQueryService().placeholder_payload("Northbridge Electronics Trading LLC.", 5000000, "紧急采购")
    task_id = create_task_record(payload, query_type="company_name", company_name=payload.name)

    context = CompanyResolverAgent().run(AgentContext(task_id=task_id, supplier={
        "id": get_task(task_id)["supplier"]["id"],
        "name": payload.name,
        "company_name": payload.name,
        "query_type": "company_name",
        "procurement_amount": 5000000,
        "cooperation_type": "紧急采购",
    }))

    assert context["supplier"]["region"] == "境外"
    assert context["supplier"]["profile_completeness"] == "低"
    assert context["supplier"]["resolution_status"] == "matched_mock_profile"
    assert any(event["agent_name"] == "CompanyResolverAgent" for event in list_events(task_id))


def test_company_resolver_agent_creates_incomplete_profile_for_unknown_name():
    service = CompanyQueryService()
    profile = service.resolve_profile("Unknown Demo Supplier Ltd.", 100000, "试单采购")

    assert profile["resolution_status"] == "incomplete_created"
    assert profile["profile_completeness"] == "低"
    assert profile["name"] == "Unknown Demo Supplier Ltd."

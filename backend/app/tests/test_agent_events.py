from app.services.task_service import TaskService


def test_agent_events_include_lifecycle_and_tool_calls():
    service = TaskService()
    task = service.create_task_from_sample("supplier_high_001")
    events = service.get_events(task["id"])

    agents = {event["agent_name"] for event in events}
    assert {"IntakeAgent", "EvidenceCollectorAgent", "ComplianceRiskAgent", "BusinessRiskAgent", "ReportAgent"}.issubset(agents)

    event_types = {(event["agent_name"], event["event_type"]) for event in events}
    for agent in ["IntakeAgent", "EvidenceCollectorAgent", "ComplianceRiskAgent", "BusinessRiskAgent", "ReportAgent"]:
        assert (agent, "agent_started") in event_types
        assert (agent, "agent_completed") in event_types

    tool_names = {event["tool_name"] for event in events if event.get("event_type") == "tool_called"}
    assert {"MockSearchTool", "EvidenceStoreTool", "RAGPolicyTool", "RiskRuleTool", "ReportExportTool"}.issubset(tool_names)

    risk_event = next(event for event in events if event.get("tool_name") == "RiskRuleTool")
    assert "raw_score=" in risk_event["tool_output_summary"]
    assert "total_score=100" in risk_event["tool_output_summary"]


def test_tool_call_events_have_clear_input_and_output_summary():
    service = TaskService()
    task = service.create_task_from_sample("medium")
    tool_events = [event for event in service.get_events(task["id"]) if event.get("event_type") == "tool_called"]

    assert tool_events
    assert all(event.get("tool_name") for event in tool_events)
    assert all(event.get("tool_input") is not None for event in tool_events)
    assert all(event.get("tool_output_summary") for event in tool_events)

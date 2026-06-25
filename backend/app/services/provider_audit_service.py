from typing import Any

from app.repositories import add_event


class ProviderAuditService:
    def event(
        self,
        task_id: str,
        event_type: str,
        status: str,
        summary: str,
        provider_name: str,
        tool_input: dict[str, Any] | None = None,
        tool_output_summary: str | None = None,
    ) -> None:
        sanitized_input = dict(tool_input or {})
        for key in list(sanitized_input):
            if "key" in key.lower() or "token" in key.lower() or "secret" in key.lower():
                sanitized_input[key] = "***"
        add_event(
            task_id,
            "EvidenceProviderManager",
            event_type,
            status,
            summary,
            tool_name=provider_name,
            tool_input=sanitized_input,
            tool_output_summary=tool_output_summary,
        )

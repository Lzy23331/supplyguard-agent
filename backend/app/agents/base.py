from typing import Any

from app.repositories import add_event


class AgentContext(dict):
    pass


class BaseAgent:
    name = "BaseAgent"

    def event(
        self,
        task_id: str,
        event_type: str,
        status: str,
        summary: str,
        tool_name: str | None = None,
        tool_input: dict[str, Any] | list[Any] | str | None = None,
        tool_output_summary: str | None = None,
    ) -> None:
        add_event(
            task_id=task_id,
            agent_name=self.name,
            event_type=event_type,
            status=status,
            summary=summary,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output_summary=tool_output_summary,
        )

    def started(self, context: AgentContext, summary: str) -> None:
        self.event(context["task_id"], "agent_started", "running", summary)

    def completed(self, context: AgentContext, summary: str) -> None:
        self.event(context["task_id"], "agent_completed", "completed", summary)

    def failed(self, context: AgentContext, summary: str) -> None:
        self.event(context["task_id"], "agent_failed", "failed", summary)

    def tool_called(
        self,
        context: AgentContext,
        tool_name: str,
        tool_input: dict[str, Any] | list[Any] | str | None,
        tool_output_summary: str,
    ) -> None:
        self.event(
            context["task_id"],
            "tool_called",
            "completed",
            f"调用工具 {tool_name}。",
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output_summary=tool_output_summary,
        )

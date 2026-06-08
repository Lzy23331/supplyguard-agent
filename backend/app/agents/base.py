from typing import Any

from app.repositories import add_event


class AgentContext(dict):
    pass


class BaseAgent:
    name = "BaseAgent"

    def event(self, task_id: str, status: str, summary: str, tool_calls: list[dict[str, Any]] | None = None) -> None:
        add_event(task_id, self.name, status, summary, tool_calls)


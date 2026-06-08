from typing import Any
from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str
    website: str | None = None
    industry: str
    region: str
    annual_spend: float = Field(ge=0)
    cooperation_type: str
    sample_key: str | None = None


class TaskCreate(BaseModel):
    supplier: SupplierCreate


class ReviewCreate(BaseModel):
    reviewer: str = "interviewer"
    decision: str
    comment: str | None = None


class AgentEvent(BaseModel):
    id: int
    task_id: str
    agent_name: str
    status: str
    summary: str
    tool_calls: list[dict[str, Any]]
    created_at: str


class TaskResponse(BaseModel):
    id: str
    status: str
    supplier: dict[str, Any]
    risk_level: str | None = None
    total_score: int | None = None
    recommendation: str | None = None
    dimensions: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    created_at: str
    updated_at: str


class ReportResponse(BaseModel):
    task_id: str
    markdown: str


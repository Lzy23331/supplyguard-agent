from typing import Any, Literal

from pydantic import BaseModel, Field

ReviewDecision = Literal["approve", "approve_with_conditions", "reject", "escalate"]
ExecutionMode = Literal["sync", "async"]
TaskStatus = Literal["pending", "running", "completed", "failed", "reviewed"]


class SupplierCreate(BaseModel):
    name: str
    website: str | None = None
    industry: str | None = None
    region: str | None = None
    annual_spend: float = Field(default=0, ge=0)
    procurement_amount: float | None = Field(default=None, ge=0)
    cooperation_type: str | None = None
    sample_key: str | None = None
    business_status: str | None = None
    company_age_years: int | None = Field(default=None, ge=0)
    profile_completeness: str | None = None
    ownership_transparency: str | None = None
    urgency: str | None = None
    summary: str | None = None
    tags: list[str] = []
    expected_risk_level: str | None = None


class TaskCreate(BaseModel):
    supplier: SupplierCreate | None = None
    supplier_id: str | None = None
    company_name: str | None = Field(default=None, min_length=1, max_length=300)
    procurement_amount: float | None = Field(default=None, ge=0)
    cooperation_type: str | None = None
    execution_mode: ExecutionMode = "sync"
    material_text: str | None = Field(default=None, max_length=20000)
    upload_ids: list[str] = []


class ReviewCreate(BaseModel):
    reviewer: str = "demo_reviewer"
    decision: ReviewDecision
    comment: str | None = None


class AgentEvent(BaseModel):
    id: int
    task_id: str
    agent_name: str
    event_type: str | None = None
    status: str
    summary: str
    tool_name: str | None = None
    tool_input: Any = None
    tool_output_summary: str | None = None
    tool_calls: list[dict[str, Any]] = []
    created_at: str


class TaskResponse(BaseModel):
    id: str
    status: TaskStatus | str
    supplier: dict[str, Any]
    risk_level: str | None = None
    total_score: int | None = None
    recommendation: str | None = None
    error_message: str | None = None
    dimensions: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    created_at: str
    updated_at: str


class ReportResponse(BaseModel):
    task_id: str
    markdown: str
    markdown_content: str | None = None

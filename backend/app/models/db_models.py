from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    sample_key: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    website: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String)
    annual_spend: Mapped[float | None] = mapped_column(Float)
    procurement_amount: Mapped[float | None] = mapped_column(Float)
    cooperation_type: Mapped[str | None] = mapped_column(String)
    business_status: Mapped[str | None] = mapped_column(String)
    company_age_years: Mapped[int | None] = mapped_column(Integer)
    profile_completeness: Mapped[str | None] = mapped_column(String)
    ownership_transparency: Mapped[str | None] = mapped_column(String)
    urgency: Mapped[str | None] = mapped_column(String)
    summary: Mapped[str | None] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON)
    expected_risk_level: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

    tasks: Mapped[list["DiligenceTask"]] = relationship(back_populates="supplier")


class DiligenceTask(Base):
    __tablename__ = "diligence_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    supplier_id: Mapped[str] = mapped_column(ForeignKey("suppliers.id"), index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    summary: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str | None] = mapped_column(String)
    total_score: Mapped[int | None] = mapped_column(Integer)
    recommendation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)

    supplier: Mapped[Supplier] = relationship(back_populates="tasks")


class EvidenceItemModel(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    task_id: Mapped[str | None] = mapped_column(String, index=True)
    supplier_id: Mapped[str | None] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    rule_signals: Mapped[list[str] | None] = mapped_column(JSON)
    economic_rationale: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str | None] = mapped_column(String, index=True)
    supplier_id: Mapped[str | None] = mapped_column(String, index=True)
    raw_score: Mapped[int | None] = mapped_column(Integer)
    total_score: Mapped[int | None] = mapped_column(Integer)
    risk_level: Mapped[str | None] = mapped_column(String)
    dimension: Mapped[str | None] = mapped_column(String)
    score: Mapped[int | None] = mapped_column(Integer)
    level: Mapped[str | None] = mapped_column(String)
    rationale: Mapped[str | None] = mapped_column(Text)
    dimension_scores: Mapped[dict | None] = mapped_column(JSON)
    triggered_rules: Mapped[list[dict] | None] = mapped_column(JSON)
    recommendation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    markdown: Mapped[str] = mapped_column(Text, nullable=False)
    markdown_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String, index=True)
    reviewer: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String, index=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    event_type: Mapped[str | None] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String)
    tool_input: Mapped[dict | None] = mapped_column(JSON)
    tool_output_summary: Mapped[str | None] = mapped_column(Text)
    tool_calls: Mapped[list[dict] | None] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String, nullable=False)

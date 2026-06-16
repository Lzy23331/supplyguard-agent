from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import Orchestrator
from app.database import init_db
from app.repositories import create_task_record, get_report, get_task, list_events, save_review
from app.schemas import ReportResponse, ReviewCreate, TaskCreate, TaskResponse
from app.services.sample_service import get_sample_supplier, list_sample_suppliers
from app.services.seed_service import seed_suppliers
from app.tools.mock_search_tool import MockSearchTool
from app.tools.rag_policy_tool import RAGPolicyTool
from app.tools.risk_rule_tool import RiskRuleTool


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_suppliers()
    yield


app = FastAPI(title="SupplyGuard Agent API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok", "service": "supplyguard-agent"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supplyguard-agent"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "SupplyGuard Agent API",
        "status": "running",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/health",
        "samples": "http://127.0.0.1:8000/api/samples/suppliers",
    }


@app.get("/api/samples/suppliers")
def samples() -> list[dict]:
    return list_sample_suppliers()


@app.get("/api/tools/mock-search/{supplier_id}")
def mock_search(supplier_id: str) -> list[dict]:
    evidence = MockSearchTool().search_by_supplier_id(supplier_id)
    if not evidence:
        raise HTTPException(status_code=404, detail=f"No mock evidence found for supplier_id={supplier_id}")
    return evidence


@app.get("/api/tools/risk-assessment/{supplier_id}")
def risk_assessment(supplier_id: str) -> dict:
    supplier = get_sample_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier not found: {supplier_id}")
    evidence = MockSearchTool().search_by_supplier_id(supplier["id"])
    return RiskRuleTool().assess(evidence, supplier)


@app.get("/api/tools/policy-search")
def policy_search(query: str = Query(..., min_length=1), top_k: int = 3) -> list[dict]:
    return RAGPolicyTool().retrieve(query, top_k=top_k)


@app.post("/api/diligence/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreate) -> dict:
    init_db()
    task_id = create_task_record(payload.supplier)
    Orchestrator().run(task_id, payload.supplier.model_dump())
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=500, detail="Task was not created")
    return task


@app.get("/api/diligence/tasks/{task_id}", response_model=TaskResponse)
def read_task(task_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/diligence/tasks/{task_id}/events")
def read_events(task_id: str) -> list[dict]:
    if not get_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return list_events(task_id)


@app.get("/api/diligence/tasks/{task_id}/report", response_model=ReportResponse)
def read_report(task_id: str) -> dict[str, str]:
    markdown = get_report(task_id)
    if markdown is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"task_id": task_id, "markdown": markdown}


@app.post("/api/diligence/tasks/{task_id}/review")
def review_task(task_id: str, payload: ReviewCreate) -> dict[str, str]:
    if not get_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    save_review(task_id, payload.reviewer, payload.decision, payload.comment)
    return {"status": "saved"}

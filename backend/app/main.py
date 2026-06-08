from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agents.orchestrator import Orchestrator
from app.database import init_db
from app.repositories import create_task_record, get_report, get_task, list_events, save_review
from app.schemas import ReportResponse, ReviewCreate, TaskCreate, TaskResponse
from app.services.samples import list_sample_suppliers


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="SupplyGuard Agent API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "SupplyGuard Agent API",
        "status": "running",
        "docs": "http://127.0.0.1:8000/docs",
        "health": "http://127.0.0.1:8000/api/health",
        "samples": "http://127.0.0.1:8000/api/samples/suppliers",
    }


@app.get("/api/samples/suppliers")
def samples() -> list[dict]:
    return list_sample_suppliers()


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

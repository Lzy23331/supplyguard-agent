from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.repositories import (
    get_report,
    get_risk_assessment,
    get_task,
    get_task_detail,
    list_events,
    list_evidence,
    list_reviews,
    list_tasks,
    save_review,
)
from app.schemas import ReviewCreate, TaskCreate
from app.services.sample_service import get_sample_supplier, list_sample_suppliers
from app.services.seed_service import seed_suppliers
from app.services.task_service import TaskService
from app.tools.mock_search_tool import MockSearchTool
from app.tools.rag_policy_tool import RAGPolicyTool
from app.tools.risk_rule_tool import RiskRuleTool


def ok(data: Any, message: str = "ok") -> dict[str, Any]:
    return {"success": True, "data": data, "message": message}


def api_error(status_code: int, code: str, message: str) -> None:
    raise HTTPException(status_code=status_code, detail={"code": code, "message": message})


def task_summary(task: dict[str, Any]) -> dict[str, Any]:
    risk = get_risk_assessment(task["id"]) or {}
    supplier = task["supplier"]
    return {
        "task_id": task["id"],
        "status": task["status"],
        "supplier_id": supplier.get("id"),
        "supplier_name": supplier.get("name"),
        "risk_level": task.get("risk_level"),
        "raw_score": risk.get("raw_score"),
        "total_score": task.get("total_score"),
        "recommendation": task.get("recommendation"),
        "summary": task.get("recommendation"),
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_suppliers()
    yield


app = FastAPI(
    title="SupplyGuard Agent API：供应商准入尽调与风险研判系统",
    version="0.4.0",
    description="本地 mock 数据驱动的供应商准入尽调、政策检索、规则评分、Agent 编排和 Markdown 报告 API。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"code": "HTTP_ERROR", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content={"success": False, "error": detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": exc.errors()}},
    )


_frontend_dist = get_settings().project_root / "frontend" / "dist"
_frontend_assets = _frontend_dist / "assets"
if _frontend_assets.exists():
    app.mount("/assets", StaticFiles(directory=_frontend_assets), name="frontend-assets")


def _frontend_ready() -> bool:
    return (_frontend_dist / "index.html").exists()


@app.get("/", response_class=HTMLResponse, summary="中文导航首页")
def root() -> str:
    app_link = '<a class="primary" href="/app">打开前端工作台</a>' if _frontend_ready() else '<span class="disabled">前端尚未构建，请先运行 npm run build</span>'
    return f"""
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>SupplyGuard Agent</title><style>body{{margin:0;font-family:"Microsoft YaHei","Segoe UI",sans-serif;background:#f6f7fb;color:#172033}}main{{max-width:1040px;margin:0 auto;padding:56px 28px}}h1{{font-size:36px;margin:0 0 10px}}p{{line-height:1.8;color:#526070}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:28px}}a,.disabled{{display:block;padding:18px;border-radius:8px;background:#fff;color:#172033;text-decoration:none;border:1px solid #d9dee8}}a:hover{{border-color:#2563eb;box-shadow:0 8px 24px rgba(37,99,235,.12)}}.primary{{background:#1f5eff;color:#fff;border-color:#1f5eff;font-weight:700}}.disabled{{color:#8b95a5}}code{{background:#e9edf5;padding:2px 6px;border-radius:4px}}</style></head>
<body><main><h1>SupplyGuard Agent</h1><p>供应商准入尽调与风险研判系统。后端服务已启动，Swagger 是 FastAPI 自动接口文档。</p><div class="grid">{app_link}<a href="/docs">打开 API 文档 / Swagger</a><a href="/health">查看健康检查 JSON</a><a href="/api/samples/suppliers">查看样例供应商 JSON</a></div></main></body></html>
"""


@app.get("/app", response_class=HTMLResponse, summary="前端工作台")
def frontend_app():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)


@app.get("/health", summary="健康检查")
def root_health() -> dict[str, Any]:
    return ok({"status": "ok", "service": "supplyguard-agent"})


@app.get("/api/health", summary="API 健康检查")
def health() -> dict[str, Any]:
    return ok({"status": "ok", "service": "supplyguard-agent"})


@app.get("/api/samples/suppliers", summary="获取样例供应商")
def samples() -> dict[str, Any]:
    return ok(list_sample_suppliers())


@app.get("/api/tools/mock-search/{supplier_id}", summary="读取供应商模拟证据")
def mock_search(supplier_id: str) -> dict[str, Any]:
    evidence = MockSearchTool().search_by_supplier_id(supplier_id)
    if not evidence:
        api_error(404, "SUPPLIER_NOT_FOUND", f"Supplier not found or no mock evidence: {supplier_id}")
    return ok(evidence)


@app.get("/api/tools/risk-assessment/{supplier_id}", summary="执行规则风险评分")
def risk_assessment(supplier_id: str) -> dict[str, Any]:
    supplier = get_sample_supplier(supplier_id)
    if not supplier:
        api_error(404, "SUPPLIER_NOT_FOUND", f"Supplier not found: {supplier_id}")
    evidence = MockSearchTool().search_by_supplier_id(supplier["id"])
    return ok(RiskRuleTool().assess(evidence, supplier))


@app.get("/api/tools/policy-search", summary="检索政策知识库")
def policy_search(query: str = Query(..., min_length=1), top_k: int = 3) -> dict[str, Any]:
    return ok(RAGPolicyTool().retrieve(query, top_k=top_k))


@app.get("/api/diligence/tasks", summary="读取最近尽调任务列表")
def read_tasks(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    return ok(list_tasks(limit=limit))


@app.post("/api/diligence/tasks", summary="创建自定义供应商尽调任务")
def create_task(payload: TaskCreate) -> dict[str, Any]:
    try:
        task = TaskService().create_task_from_payload(payload.supplier)
        return ok(task_summary(task), "task completed")
    except Exception as exc:
        api_error(500, "TASK_EXECUTION_FAILED", str(exc))


@app.post("/api/diligence/tasks/from-sample/{supplier_id}", summary="从样例供应商创建尽调任务")
def create_task_from_sample(supplier_id: str) -> dict[str, Any]:
    try:
        task = TaskService().create_task_from_sample(supplier_id)
        return ok(task_summary(task), "task completed")
    except ValueError:
        api_error(404, "SUPPLIER_NOT_FOUND", f"Supplier not found: {supplier_id}")
    except Exception as exc:
        api_error(500, "TASK_EXECUTION_FAILED", str(exc))


@app.get("/api/diligence/tasks/{task_id}", summary="读取尽调任务详情")
def read_task(task_id: str) -> dict[str, Any]:
    detail = get_task_detail(task_id)
    if not detail:
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    return ok(detail)


@app.get("/api/diligence/tasks/{task_id}/events", summary="读取 Agent 执行事件")
def read_events(task_id: str) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    return ok(list_events(task_id))


@app.get("/api/diligence/tasks/{task_id}/evidence", summary="读取任务证据链")
def read_evidence(task_id: str) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    return ok(list_evidence(task_id))


@app.get("/api/diligence/tasks/{task_id}/report", summary="读取尽调报告")
def read_report(task_id: str) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    markdown = get_report(task_id)
    if markdown is None:
        api_error(404, "REPORT_NOT_FOUND", f"Report not found: {task_id}")
    return ok({"task_id": task_id, "markdown_content": markdown})


@app.post("/api/diligence/tasks/{task_id}/review", summary="保存人工复核意见")
def review_task(task_id: str, payload: ReviewCreate) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    review = save_review(task_id, payload.reviewer, payload.decision, payload.comment)
    review["reviews"] = list_reviews(task_id)
    return ok(review, "review submitted")



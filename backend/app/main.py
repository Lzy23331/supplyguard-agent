from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
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
    task_diagnostics,
    save_review,
)
from app.schemas import ReviewCreate, TaskCreate
from app.services.sample_service import get_sample_supplier, list_sample_suppliers
from app.services.async_task_service import run_diligence_task_background
from app.services.demo_case_service import DemoCaseService
from app.services.file_service import get_upload_record, save_and_parse_material_file
from app.services.pdf_report_service import PDFReportService
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
    diagnostics = task_diagnostics(task["id"])
    return {
        "task_id": task["id"],
        "id": task["id"],
        "status": task["status"],
        "supplier_id": supplier.get("id"),
        "supplier_name": supplier.get("name"),
        "risk_level": task.get("risk_level"),
        "raw_score": risk.get("raw_score"),
        "total_score": task.get("total_score"),
        "recommendation": task.get("recommendation"),
        "error_message": task.get("error_message"),
        "summary": task.get("recommendation"),
        "created_at": task.get("created_at"),
        "updated_at": task.get("updated_at"),
        "cooperation_type": supplier.get("cooperation_type"),
        "procurement_amount": supplier.get("procurement_amount"),
        **{key: diagnostics[key] for key in [
            "provider_mode",
            "search_query_count",
            "web_search_result_count",
            "real_url_count",
            "profile_snapshot_count",
            "profile_non_empty_count",
            "scoring_evidence_count",
            "report_available",
        ]},
    }



def _mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    tail = value[-4:] if len(value) >= 4 else value
    return f"****{tail}"


def _provider_status() -> dict[str, Any]:
    settings = get_settings()
    tencent_configured = bool(settings.tencentcloud_secret_id and settings.tencentcloud_secret_key)
    llm_configured = bool(settings.openai_api_key)
    real_provider_requested = settings.web_search_provider == "real" or settings.provider_mode == "real"
    return {
        "deployment_mode": settings.deployment_mode,
        "real_query_enabled": bool((settings.enable_real_query or real_provider_requested) and tencent_configured),
        "real_query_requested": bool(settings.enable_real_query or real_provider_requested),
        "tencent_search_configured": tencent_configured,
        "llm_configured": llm_configured,
        "pdf_export_available": True,
        "demo_mode_available": True,
        "web_search_provider": settings.web_search_provider,
        "web_search_api": settings.web_search_api,
        "llm_model": settings.openai_model if llm_configured else None,
        "tencent_secret_id_mask": _mask_secret(settings.tencentcloud_secret_id),
        "api_key_mask": _mask_secret(settings.openai_api_key),
    }

def upload_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "upload_id": record["id"],
        "filename": record.get("original_filename") or record.get("filename"),
        "file_type": record.get("file_type"),
        "status": record.get("status"),
        "text_length": record.get("text_length") or 0,
        "summary": record.get("summary"),
        "error_message": record.get("error_message"),
        "created_at": record.get("created_at"),
        "updated_at": record.get("updated_at"),
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


@app.get("/", response_class=HTMLResponse, summary="演示网站首页")
def root():
    index_path = _frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>SupplyGuard Agent</h1><p>前端尚未构建，请先运行 npm run build。</p>", status_code=200)


@app.get("/app", response_class=HTMLResponse, summary="前端工作台")
def frontend_app():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)




@app.get("/demo", response_class=HTMLResponse, summary="前端 Demo 案例页")
def frontend_demo():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)


@app.get("/settings/status", response_class=HTMLResponse, summary="前端 Provider 状态页")
def frontend_provider_status():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)

@app.get("/tasks", response_class=HTMLResponse, summary="前端任务列表页")
def frontend_tasks():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)


@app.get("/tasks/{task_id}", response_class=HTMLResponse, summary="前端任务详情页")
def frontend_task_detail(task_id: str):
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



@app.get("/api/system/provider-status", summary="读取 Provider 与部署状态")
def provider_status() -> dict[str, Any]:
    return ok(_provider_status())


@app.get("/api/demo-cases", summary="读取缓存演示案例列表")
def list_demo_cases() -> dict[str, Any]:
    return ok(DemoCaseService().list_cases())


@app.get("/api/demo-cases/{case_id}/preview", summary="读取缓存演示案例预览")
def preview_demo_case(case_id: str) -> dict[str, Any]:
    try:
        return ok(DemoCaseService().preview(case_id))
    except ValueError as exc:
        api_error(404, "DEMO_CASE_NOT_FOUND", str(exc))


@app.post("/api/demo-cases/{case_id}/run", summary="创建缓存演示任务")
def run_demo_case(case_id: str) -> dict[str, Any]:
    try:
        return ok(DemoCaseService().run_case(case_id), "cached demo task created")
    except ValueError as exc:
        api_error(404, "DEMO_CASE_NOT_FOUND", str(exc))

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


@app.post("/api/uploads/materials", summary="上传并解析供应商材料")
def upload_material(file: UploadFile = File(...)) -> dict[str, Any]:
    try:
        record = save_and_parse_material_file(file.filename or "material.txt", file.file)
        return ok(upload_summary(record), "file uploaded")
    except ValueError as exc:
        api_error(400, "UPLOAD_REJECTED", str(exc))
    except Exception as exc:
        api_error(500, "UPLOAD_FAILED", str(exc))


@app.get("/api/uploads/{upload_id}", summary="读取上传材料解析状态")
def read_upload(upload_id: str) -> dict[str, Any]:
    record = get_upload_record(upload_id)
    if not record:
        api_error(404, "UPLOAD_NOT_FOUND", f"Upload not found: {upload_id}")
    return ok(upload_summary(record))


@app.get("/api/diligence/tasks", summary="读取最近尽调任务列表")
def read_tasks(limit: int = Query(default=20, ge=1, le=100)) -> dict[str, Any]:
    return ok(list_tasks(limit=limit))


@app.post("/api/diligence/tasks", summary="创建供应商尽调任务")
def create_task(payload: TaskCreate, background_tasks: BackgroundTasks) -> dict[str, Any]:
    try:
        service = TaskService()
        if payload.company_name:
            if payload.execution_mode == "async":
                task = service.create_pending_task_from_company_query(
                    payload.company_name,
                    procurement_amount=payload.procurement_amount,
                    cooperation_type=payload.cooperation_type,
                    material_text=payload.material_text,
                    upload_ids=payload.upload_ids,
                )
                background_tasks.add_task(run_diligence_task_background, task["id"])
                return ok(task_summary(task), "task accepted")
            task = service.create_task_from_company_query(
                payload.company_name,
                procurement_amount=payload.procurement_amount,
                cooperation_type=payload.cooperation_type,
                material_text=payload.material_text,
                upload_ids=payload.upload_ids,
            )
            return ok(task_summary(task), "task completed")
        if payload.supplier_id:
            if payload.execution_mode == "async":
                task = service.create_pending_task_from_sample(payload.supplier_id, material_text=payload.material_text, upload_ids=payload.upload_ids)
                background_tasks.add_task(run_diligence_task_background, task["id"])
                return ok(task_summary(task), "task accepted")
            task = service.create_task_from_sample(payload.supplier_id, material_text=payload.material_text, upload_ids=payload.upload_ids)
            return ok(task_summary(task), "task completed")
        if not payload.supplier:
            api_error(422, "SUPPLIER_REQUIRED", "supplier, supplier_id or company_name is required")
        if payload.execution_mode == "async":
            task = service.create_pending_task_from_payload(payload.supplier, material_text=payload.material_text, upload_ids=payload.upload_ids)
            background_tasks.add_task(run_diligence_task_background, task["id"])
            return ok(task_summary(task), "task accepted")
        task = service.create_task_from_payload(payload.supplier, material_text=payload.material_text, upload_ids=payload.upload_ids)
        return ok(task_summary(task), "task completed")
    except HTTPException:
        raise
    except ValueError:
        api_error(404, "SUPPLIER_NOT_FOUND", f"Supplier not found: {payload.supplier_id}")
    except Exception as exc:
        api_error(500, "TASK_EXECUTION_FAILED", str(exc))


@app.post("/api/diligence/tasks/from-sample/{supplier_id}", summary="从样例供应商创建尽调任务")
def create_task_from_sample(
    supplier_id: str,
    background_tasks: BackgroundTasks,
    execution_mode: str = Query(default="sync", pattern="^(sync|async)$"),
) -> dict[str, Any]:
    try:
        service = TaskService()
        if execution_mode == "async":
            task = service.create_pending_task_from_sample(supplier_id)
            background_tasks.add_task(run_diligence_task_background, task["id"])
            return ok(task_summary(task), "task accepted")
        task = service.create_task_from_sample(supplier_id)
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
    if f"任务 ID：{task_id}" not in markdown and f"任务ID：{task_id}" not in markdown:
        markdown = markdown.replace("## 1. 基本信息", f"## 1. 基本信息\n- 任务 ID：{task_id}", 1)
    return ok({"task_id": task_id, "filename": f"supplyguard-report-{task_id}.md", "markdown_content": markdown})


@app.get("/api/diligence/tasks/{task_id}/diagnostics", summary="读取任务搜索与画像对账数据")
def read_task_diagnostics(task_id: str) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    return ok(task_diagnostics(task_id))



@app.get("/api/diligence/tasks/{task_id}/report.pdf", summary="下载 PDF 尽调报告")
def read_report_pdf(task_id: str) -> Response:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    markdown = get_report(task_id)
    if markdown is None:
        api_error(404, "REPORT_NOT_FOUND", f"Report not found: {task_id}")
    pdf = PDFReportService().render(markdown, task_id=task_id)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="supplyguard-report-{task_id}.pdf"'},
    )
@app.post("/api/diligence/tasks/{task_id}/review", summary="保存人工复核意见")
def review_task(task_id: str, payload: ReviewCreate) -> dict[str, Any]:
    if not get_task(task_id):
        api_error(404, "TASK_NOT_FOUND", f"Task not found: {task_id}")
    review = save_review(task_id, payload.reviewer, payload.decision, payload.comment)
    review["reviews"] = list_reviews(task_id)
    return ok(review, "review submitted")







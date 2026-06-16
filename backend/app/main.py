from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.agents.orchestrator import Orchestrator
from app.config import get_settings
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


app = FastAPI(
    title="SupplyGuard Agent API：供应商准入尽调与风险研判系统",
    version="0.2.0",
    description="本地 mock 数据驱动的供应商准入尽调、政策检索和规则评分 API。",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SupplyGuard Agent</title>
  <style>
    body {{ margin: 0; font-family: "Microsoft YaHei", "Segoe UI", sans-serif; background: #f6f7fb; color: #172033; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 56px 28px; }}
    h1 {{ font-size: 36px; margin: 0 0 10px; }}
    p {{ line-height: 1.8; color: #526070; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 28px; }}
    a, .disabled {{ display: block; padding: 18px; border-radius: 8px; background: #fff; color: #172033; text-decoration: none; border: 1px solid #d9dee8; }}
    a:hover {{ border-color: #2563eb; box-shadow: 0 8px 24px rgba(37, 99, 235, 0.12); }}
    .primary {{ background: #1f5eff; color: #fff; border-color: #1f5eff; font-weight: 700; }}
    .disabled {{ color: #8b95a5; }}
    code {{ background: #e9edf5; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <main>
    <h1>SupplyGuard Agent</h1>
    <p>供应商准入尽调与风险研判系统。后端服务已启动，当前页面是中文导航首页；Swagger 仍是 FastAPI 自动文档，用于开发调试。</p>
    <div class="grid">
      {app_link}
      <a href="/docs">打开 API 文档 / Swagger</a>
      <a href="/health">查看健康检查 JSON</a>
      <a href="/api/samples/suppliers">查看样例供应商 JSON</a>
      <a href="/api/tools/risk-assessment/supplier_high_001">查看高风险样例评分 JSON</a>
      <a href="/api/tools/policy-search?query=制裁名单%20黑名单%20境外供应商">测试政策检索 JSON</a>
    </div>
    <p>如果要开发前端，请打开 <code>http://127.0.0.1:5173</code>；如果只运行后端，构建后的前端可通过 <code>/app</code> 访问。</p>
  </main>
</body>
</html>
"""


@app.get("/app", response_class=HTMLResponse, summary="前端工作台")
def frontend_app():
    index_path = _frontend_dist / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>前端尚未构建</h1><p>请先在 frontend 目录运行 npm run build。</p>", status_code=404)
    return FileResponse(index_path)


@app.get("/health", summary="健康检查")
def root_health() -> dict[str, str]:
    return {"status": "ok", "service": "supplyguard-agent"}


@app.get("/api/health", summary="API 健康检查")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "supplyguard-agent"}


@app.get("/api/samples/suppliers", summary="获取样例供应商")
def samples() -> list[dict]:
    return list_sample_suppliers()


@app.get("/api/tools/mock-search/{supplier_id}", summary="读取供应商模拟证据")
def mock_search(supplier_id: str) -> list[dict]:
    evidence = MockSearchTool().search_by_supplier_id(supplier_id)
    if not evidence:
        raise HTTPException(status_code=404, detail=f"No mock evidence found for supplier_id={supplier_id}")
    return evidence


@app.get("/api/tools/risk-assessment/{supplier_id}", summary="执行规则风险评分")
def risk_assessment(supplier_id: str) -> dict:
    supplier = get_sample_supplier(supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail=f"Supplier not found: {supplier_id}")
    evidence = MockSearchTool().search_by_supplier_id(supplier["id"])
    return RiskRuleTool().assess(evidence, supplier)


@app.get("/api/tools/policy-search", summary="检索政策知识库")
def policy_search(query: str = Query(..., min_length=1), top_k: int = 3) -> list[dict]:
    return RAGPolicyTool().retrieve(query, top_k=top_k)


@app.post("/api/diligence/tasks", response_model=TaskResponse, summary="创建尽调任务")
def create_task(payload: TaskCreate) -> dict:
    init_db()
    task_id = create_task_record(payload.supplier)
    Orchestrator().run(task_id, payload.supplier.model_dump())
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=500, detail="Task was not created")
    return task


@app.get("/api/diligence/tasks/{task_id}", response_model=TaskResponse, summary="读取尽调任务")
def read_task(task_id: str) -> dict:
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/diligence/tasks/{task_id}/events", summary="读取 Agent 执行事件")
def read_events(task_id: str) -> list[dict]:
    if not get_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return list_events(task_id)


@app.get("/api/diligence/tasks/{task_id}/report", response_model=ReportResponse, summary="读取尽调报告")
def read_report(task_id: str) -> dict[str, str]:
    markdown = get_report(task_id)
    if markdown is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"task_id": task_id, "markdown": markdown}


@app.post("/api/diligence/tasks/{task_id}/review", summary="保存人工复核意见")
def review_task(task_id: str, payload: ReviewCreate) -> dict[str, str]:
    if not get_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    save_review(task_id, payload.reviewer, payload.decision, payload.comment)
    return {"status": "saved"}


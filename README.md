# SupplyGuard Agent

SupplyGuard Agent 是一个供应商准入尽调与风险研判演示网站。系统将企业名称查询、联网搜索计划、公开网页结果可信度评估、企业画像抽取、规则评分、证据链报告和 Markdown/PDF 导出串成一个完整 AI Agent 闭环。

## 演示模式

- **Cached Demo Mode（默认）**：使用预置华为、小米、比亚迪等案例，不消耗腾讯云或 LLM API，适合线上简历展示。
- **Real Query Mode（可选）**：仅当后端设置 `ENABLE_REAL_QUERY=true` 且腾讯云/LLM 密钥均配置时，用真实 API 执行实时查询。

## 核心能力

- LLM/SearchQueryPlanner 生成搜索计划。
- TencentWebSearchProvider 或缓存数据产生公开网页搜索结果。
- SearchEvidenceQualityEvaluator 区分目标签约主体、关联主体、品牌新闻和普通搜索记录。
- CompanyProfileExtractionAgent 抽取企业画像字段并保留来源 URL。
- RiskRuleTool 依据可评分证据和资料完整性/采购暴露计算风险等级。
- ReportAgent 输出可对账 Markdown 报告，PDF 导出支持中文。
- `/tasks/{task_id}` 详情页确保页面、报告和数据库属于同一个 task_id。

## 本地运行

```powershell
cd D:\projects\SupplyGuard-Agent
.\.venv\Scripts\python.exe scripts\seed_demo_cases.py
cd frontend
npm install
npm run build
cd ..\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

打开：`http://127.0.0.1:8000`

开发模式前端：

```powershell
cd D:\projects\SupplyGuard-Agent\frontend
npm run dev -- --host 127.0.0.1
```

## 环境变量

参考 `.env.example`。密钥只能配置在后端 `.env` 或部署平台 Secret 中，不得进入 React 前端、Git、报告或 PDF。

## 主要页面

- `/`：Landing Page
- `/demo`：缓存 Demo Case Gallery
- `/tasks`：历史任务列表
- `/tasks/{task_id}`：任务详情、证据链、报告下载
- `/settings/status`：Provider 配置状态，密钥仅 masked 显示

## 免责声明

本项目用于技术演示。缓存案例基于公开网页摘要和模拟数据，不构成采购、法律、投资或合规意见。正式准入需人工复核并以官方工商、司法、制裁及内部系统核验为准。

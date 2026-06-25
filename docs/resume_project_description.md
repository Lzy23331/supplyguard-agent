# Resume Project Description

## 150 字版

SupplyGuard Agent 是一个供应商准入尽调 AI Agent 网站，支持企业名称查询、联网搜索计划、公开网页证据可信度评估、企业画像抽取、规则评分和 Markdown/PDF 报告导出。系统提供 Cached Demo Mode，适合稳定线上演示；同时保留可选 Real Query Mode 接入腾讯云搜索和 DeepSeek/OpenAI-compatible LLM。

## 300 字版

SupplyGuard Agent 面向采购准入与供应商合规场景，构建了从企业输入到报告导出的完整 AI Agent 闭环。后端基于 FastAPI 编排 SearchQueryPlannerAgent、TencentWebSearchProvider、SearchEvidenceQualityEvaluator、CompanyProfileExtractionAgent、RiskRuleTool 和 ReportAgent；前端基于 React 展示 Demo 案例、历史任务、task_id 对账、搜索结果、企业画像、证据链和报告导出。系统区分真实风险证据、普通搜索记录、关联主体新闻和同名企业结果，降低自动评分误伤。默认 Cached Demo Mode 不消耗 API，适合简历展示；Real Query Mode 可在后端配置密钥后开启。

## 要点版

- FastAPI + React + SQLite + 腾讯云联网搜索 + DeepSeek/OpenAI-compatible LLM。
- 缓存演示案例和实时查询双模式。
- 搜索结果可信度评估、同名企业消歧、证据是否参与评分分离。
- 企业画像字段级来源 URL、置信度和人工复核标记。
- Markdown/PDF 报告导出，文件名和正文绑定 task_id。
- Provider 状态页 masked key 展示，避免密钥泄漏。

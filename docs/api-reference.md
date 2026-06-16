# SupplyGuard Agent API Reference

## 统一响应结构

成功响应：

```json
{
  "success": true,
  "data": {},
  "message": "ok"
}
```

错误响应：

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task not found: ..."
  }
}
```

常见错误码：

| code | HTTP | 含义 |
| --- | ---: | --- |
| `SUPPLIER_NOT_FOUND` | 404 | 样例供应商不存在 |
| `TASK_NOT_FOUND` | 404 | 尽调任务不存在 |
| `REPORT_NOT_FOUND` | 404 | 报告尚未生成或不存在 |
| `VALIDATION_ERROR` | 422 | 请求字段缺失或类型错误 |
| `TASK_EXECUTION_FAILED` | 500 | Agent 工作流执行失败 |

## API 总览

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/health` | 健康检查 |
| GET | `/api/samples/suppliers` | 获取样例供应商卡片数据 |
| POST | `/api/diligence/tasks/from-sample/{supplier_id}` | 从样例供应商创建同步尽调任务 |
| POST | `/api/diligence/tasks` | 创建自定义供应商尽调任务 |
| GET | `/api/diligence/tasks` | 获取最近任务列表 |
| GET | `/api/diligence/tasks/{task_id}` | 获取任务详情和风险评估 |
| GET | `/api/diligence/tasks/{task_id}/events` | 获取 Agent 执行事件 |
| GET | `/api/diligence/tasks/{task_id}/evidence` | 获取证据链 |
| GET | `/api/diligence/tasks/{task_id}/report` | 获取 Markdown 报告 |
| POST | `/api/diligence/tasks/{task_id}/review` | 提交人工复核结论 |

## 样例供应商

`GET /api/samples/suppliers` 返回 3 个样例，每个样例至少包含：

```json
{
  "id": "supplier_high_001",
  "sample_key": "high",
  "name": "Redstone Metals Trading",
  "industry": "金属贸易",
  "region": "中国香港",
  "procurement_amount": 2600000,
  "cooperation_type": "关键原材料供应商",
  "business_status": "信息不透明",
  "profile_completeness": "低",
  "ownership_transparency": "低",
  "urgency": "紧急",
  "summary": "存在制裁接近性与商业贿赂相关指控，构成严重合规风险。",
  "tags": ["制裁接近", "商业贿赂"],
  "expected_risk_level": "high"
}
```

前端使用方式：渲染 low/medium/high 样例供应商卡片，并将 `id` 传给从样例创建任务接口。

## 创建任务

### 从样例创建

`POST /api/diligence/tasks/from-sample/supplier_high_001`

响应 `data`：

```json
{
  "task_id": "...",
  "status": "completed",
  "supplier_id": "supplier_high_001",
  "supplier_name": "Redstone Metals Trading",
  "risk_level": "high",
  "raw_score": 250,
  "total_score": 100,
  "recommendation": "建议拒绝准入；如业务必须采购，应升级至合规委员会或管理层审批。",
  "summary": "..."
}
```

### 创建自定义任务

`POST /api/diligence/tasks`

```json
{
  "supplier": {
    "name": "Demo Supplier Ltd.",
    "website": "https://example.com/demo",
    "industry": "电子元器件",
    "region": "广东深圳",
    "procurement_amount": 800000,
    "annual_spend": 800000,
    "cooperation_type": "标准采购",
    "business_status": "正常",
    "company_age_years": 5,
    "profile_completeness": "中",
    "ownership_transparency": "中",
    "urgency": "常规"
  }
}
```

自定义供应商可以没有 mock 证据。系统会保存基础资料证据，并根据采购金额、资料完整性、经营状态等字段计算风险。

## 任务列表与详情

`GET /api/diligence/tasks` 返回最近任务列表，用于前端历史任务页。

`GET /api/diligence/tasks/{task_id}` 返回：

```json
{
  "task": {"id": "...", "status": "completed", "summary": "...", "created_at": "...", "updated_at": "..."},
  "supplier": {},
  "risk_assessment": {
    "raw_score": 250,
    "total_score": 100,
    "risk_level": "high",
    "dimension_scores": {},
    "triggered_rules": [],
    "recommendation": "..."
  }
}
```

前端使用方式：详情页展示任务状态、供应商画像、综合风险和命中规则。

## 事件、证据与报告

`GET /events` 返回 Agent 时间线字段：`id`、`agent_name`、`event_type`、`status`、`summary`、`tool_name`、`tool_input`、`tool_output_summary`、`created_at`。

`GET /evidence` 返回证据卡片字段：`id`、`source`、`category`、`title`、`content`、`severity`、`rule_signals`、`economic_rationale`、`url`、`created_at`。

`GET /report` 返回：

```json
{
  "task_id": "...",
  "markdown_content": "# 供应商准入尽调报告\n..."
}
```

前端使用方式：分别渲染 Agent 时间线、关键证据链和 Markdown 报告。

## 人工复核

`POST /api/diligence/tasks/{task_id}/review`

```json
{
  "reviewer": "demo_reviewer",
  "decision": "approve_with_conditions",
  "comment": "要求供应商补充合规证明和近三年交付记录后再准入。"
}
```

允许的 `decision`：`approve`、`approve_with_conditions`、`reject`、`escalate`。

提交成功后写入 `human_reviews`，并将任务状态更新为 `reviewed`。

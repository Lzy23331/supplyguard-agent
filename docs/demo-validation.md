# Demo Validation

## 自动化验证

在项目根目录运行：

```powershell
cd "D:\projects\SupplyGuard-Agent"
$env:PYTHONPATH="D:\projects\SupplyGuard-Agent\backend"
.\.venv\Scripts\python.exe -m pytest backend\app\tests
```

当前第四批验证结果：`33 passed`。

## 手动验收流程

1. 启动后端。

```powershell
cd "D:\projects\SupplyGuard-Agent"
.\scripts\start-backend.ps1
```

2. 打开 Swagger。

```text
http://127.0.0.1:8000/docs
```

3. 检查健康接口。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

4. 获取样例供应商。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/samples/suppliers"
```

5. 创建 low、medium、high 三个样例任务。

```powershell
$low = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_low_001"
$medium = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_medium_001"
$high = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_high_001"
$high.data
```

期望：`high.data.risk_level = high`，`high.data.total_score = 100`。

6. 查看 high 任务详情。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($high.data.task_id)"
```

7. 查看 high 事件链。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($high.data.task_id)/events"
```

期望：包含 IntakeAgent、EvidenceCollectorAgent、ComplianceRiskAgent、BusinessRiskAgent、ReportAgent 的开始、工具调用和完成事件。

8. 查看 high 证据链。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($high.data.task_id)/evidence"
```

期望：证据包含 `rule_signals`、`economic_rationale` 和 `severity=critical` 的高风险证据。

9. 查看 high Markdown 报告。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($high.data.task_id)/report"
```

期望：`data.markdown_content` 以 `# 供应商准入尽调报告` 开头。

10. 提交人工复核。

```powershell
$review = @{ reviewer="demo_reviewer"; decision="approve_with_conditions"; comment="要求供应商补充合规证明和近三年交付记录后再准入。" } | ConvertTo-Json
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/$($high.data.task_id)/review" -ContentType "application/json" -Body $review
```

期望：响应 `message=review submitted`，再次查看任务详情时 `task.status=reviewed`。

11. 创建自定义供应商任务。

```powershell
$body = @{ supplier = @{ name="Demo Supplier Ltd."; website="https://example.com/demo"; industry="电子元器件"; region="广东深圳"; procurement_amount=800000; annual_spend=800000; cooperation_type="标准采购"; business_status="正常"; company_age_years=5; profile_completeness="中"; ownership_transparency="中"; urgency="常规" } } | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks" -ContentType "application/json" -Body $body
```

期望：即使没有 mock 证据，也能同步完成任务并生成事件和报告。

12. 查看任务列表。

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks"
```

## 第三批与第四批验收记录

第三批能力已覆盖：Agent 编排、agent_events、证据链保存、规则评分、RAG 政策检索和 Markdown 报告生成。

第四批新增验收点：统一 API 响应结构、样例任务创建、自定义任务创建、任务列表、稳定详情结构、事件/证据/报告接口、人工复核、错误码和 API 文档。

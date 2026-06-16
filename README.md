# SupplyGuard Agent

SupplyGuard Agent 是一个供应商准入尽调与风险研判系统，用于展示企业采购风控场景下的工程化 Agent 工作流。系统通过本地模拟数据、政策知识库、确定性规则引擎和可追溯 Agent 事件，完成供应商证据收集、风险评分和 Markdown 尽调报告生成。

> 本项目仅用于学习、演示和求职作品集展示。当前版本使用本地 mock 数据，不接入真实工商、司法、制裁、新闻或合规数据库，不构成真实法律、合规或商业决策建议。

## 项目路径

推荐统一使用：

```powershell
D:\projects\supplyguard-agent
```

如果你的本地目录仍是 `D:\projects\SupplyGuard-Agent`，命令也可以运行；README 中统一写推荐路径，是为了避免带空格路径造成 PowerShell、Python、npm 或后续工具调用问题。

## 你看到的几个页面分别是什么

- `http://127.0.0.1:8000/`：中文导航首页，适合从后端入口进入项目。
- `http://127.0.0.1:8000/docs`：FastAPI 自动生成的 Swagger API 文档，主要给开发者调试接口，界面本身会保留 Swagger 风格。
- `http://127.0.0.1:8000/health`：健康检查 JSON，不是前端页面。
- `http://127.0.0.1:8000/api/samples/suppliers`：样例供应商 JSON，不是前端页面。
- `http://127.0.0.1:5173`：Vite 开发模式下的 React 前端工作台。
- `http://127.0.0.1:8000/app`：后端托管的前端构建产物，需要先运行 `npm run build`。

## 独立 Python 环境

项目使用根目录下的独立虚拟环境：

```text
D:\projects\supplyguard-agent\.venv
```

首次准备后端环境：

```powershell
cd "D:\projects\supplyguard-agent"
.\scripts\setup-backend-env.ps1
```

这个脚本会创建 `.venv` 并安装 `backend\requirements.txt`。

后续启动后端：

```powershell
cd "D:\projects\supplyguard-agent"
.\scripts\start-backend.ps1
```

`start-backend.ps1` 会强制使用项目 `.venv\Scripts\python.exe`，避免误用系统 Python 或其他 conda 环境。

## 前端启动

开发模式：

```powershell
cd "D:\projects\supplyguard-agent"
.\scripts\start-frontend.ps1
```

打开：

```text
http://127.0.0.1:5173
```

如果希望只通过后端端口访问前端，请先构建：

```powershell
cd "D:\projects\supplyguard-agent\frontend"
npm run build
```

然后启动后端并打开：

```text
http://127.0.0.1:8000/app
```

## 当前项目边界

第一版优先保证稳定、可复现、可讲解：

- 不依赖真实 LLM API。
- 不依赖真实外部数据接口。
- 不使用复杂向量数据库，政策检索先采用本地 Markdown + 关键词检索。
- 风险分数和风险等级由规则引擎计算，不交给 LLM 随意判断。
- 所有关键过程写入 SQLite 和 agent events，方便前端展示与面试讲解。

## 样例供应商

程序内部风险等级统一为 `low`、`medium`、`high`；前端和报告展示为低风险、中风险、高风险。

| 样例 | 供应商 | 关键特征 | 内部等级 | 展示标签 | 建议 |
| --- | --- | --- | --- | --- | --- |
| low | Aster Precision Components Co., Ltd. | 资料完整、经营稳定、无重大负面 | low | 低风险 | 建议准入 |
| medium | Nova Packaging Materials Ltd. | 交付延期、轻微合同争议、年度框架金额较高、需补充履约材料 | medium | 中风险 | 补充材料后准入或人工复核 |
| high | Northbridge Electronics Trading LLC | 境外信息不透明、紧急高额采购、疑似制裁/黑名单、多条纠纷 | high | 高风险 | 拒绝准入或升级审批 |

## 风险模型

规则引擎从 0 分开始，根据证据和供应商画像累加风险分：

- `raw_score`：所有命中规则累加后的原始分。
- `total_score`：对外展示和入库的分数，计算方式为 `min(raw_score, 100)`。
- `triggered_rules`：每条命中规则、所属维度、分值、原因和证据来源。

| 分数 | 内部等级 | 展示标签 | 处置 |
| --- | --- | --- | --- |
| 0-39 | low | 低风险 | 建议准入，按年度复查 |
| 40-69 | medium | 中风险 | 补充材料后准入，或进入人工复核 |
| 70-100 | high | 高风险 | 拒绝准入或升级审批 |

## 常用验证命令

```powershell
cd "D:\projects\supplyguard-agent"
$env:PYTHONPATH="D:\projects\supplyguard-agent\backend"
.\.venv\Scripts\python.exe -m pytest .\backend\app\tests
```

前端构建验证：

```powershell
cd "D:\projects\supplyguard-agent\frontend"
npm run build
```

## API 示例

高风险评分：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/tools/risk-assessment/supplier_high_001"
```

政策检索：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/tools/policy-search?query=制裁名单%20黑名单%20境外供应商"
```
从样例供应商创建完整 Agent 尽调任务：

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_high_001"
```

读取任务事件、证据和报告：

```powershell
$task = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_medium_001"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.id)/events"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.id)/evidence"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.id)/report"
```

## 后续批次

1. 第三批：完善 Agent 工作流和 Orchestrator。
2. 第四批：完善 HTTP API、Swagger 验证和后端测试。
3. 第五批：完善 React 前端工作台。
4. 第六批：完善文档、演示脚本、面试讲解和最终测试。


## 第四批 API 使用示例

后端启动：

```powershell
cd "D:\projects\SupplyGuard-Agent"
.\scripts\start-backend.ps1
```

打开 Swagger：`http://127.0.0.1:8000/docs`

健康检查：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/health"
```

获取样例供应商：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/samples/suppliers"
```

从高风险样例创建任务：

```powershell
$task = Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/from-sample/supplier_high_001"
$task.data.task_id
```

创建自定义供应商任务：

```powershell
$body = @{
  supplier = @{
    name = "Demo Supplier Ltd."
    website = "https://example.com/demo"
    industry = "电子元器件"
    region = "广东深圳"
    procurement_amount = 800000
    annual_spend = 800000
    cooperation_type = "标准采购"
    business_status = "正常"
    company_age_years = 5
    profile_completeness = "中"
    ownership_transparency = "中"
    urgency = "常规"
  }
} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks" -ContentType "application/json" -Body $body
```

查询任务列表、详情、事件、证据和报告：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.data.task_id)"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.data.task_id)/events"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.data.task_id)/evidence"
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/$($task.data.task_id)/report"
```

提交人工复核：

```powershell
$review = @{ reviewer="demo_reviewer"; decision="approve_with_conditions"; comment="要求供应商补充合规证明和近三年交付记录后再准入。" } | ConvertTo-Json
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks/$($task.data.task_id)/review" -ContentType "application/json" -Body $review
```

所有第四批核心 API 均使用统一响应结构：成功为 `{ success, data, message }`，失败为 `{ success:false, error:{ code, message } }`。

## 第五批前端工作台

前端工作台用于演示供应商尽调任务的完整闭环：样例任务、自定义任务、风险画像、Agent 时间线、证据链、Markdown 报告和人工复核。

启动后端：

```powershell
cd "D:\projects\SupplyGuard-Agent"
.\scripts\start-backend.ps1
```

启动前端：

```powershell
cd "D:\projects\SupplyGuard-Agent\frontend"
npm install
npm run dev
```

如果使用项目内便携 Node：

```powershell
cd "D:\projects\SupplyGuard-Agent"
.\scripts\start-frontend.ps1
```

访问：`http://127.0.0.1:5173`

演示流程：

1. 在任务创建页查看低/中/高风险样例供应商卡片。
2. 点击“创建该样例任务”，推荐使用高风险样例。
3. 进入任务详情页，确认风险等级为“高风险”，总分为 `100`，原始分为 `250`。
4. 查看 Agent 执行时间线，确认五个 Agent 和工具调用均展示。
5. 查看关键证据链，确认制裁接近性、商业贿赂等高风险证据可见。
6. 查看 Markdown 尽调报告，点击“复制报告”或“下载 Markdown”。
7. 在人工复核区域选择复核结论并提交，页面提示“人工复核已提交”。
8. 返回任务创建页，使用自定义供应商表单创建自定义尽调任务。

前端 API 地址可通过 `frontend/.env.example` 配置：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```

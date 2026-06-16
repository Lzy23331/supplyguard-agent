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


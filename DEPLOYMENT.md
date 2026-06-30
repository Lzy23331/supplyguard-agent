# Deployment Guide

推荐部署方式：Render Web Service + Docker。后端 FastAPI 同时服务 API 与前端 `frontend/dist`，部署后访问根路径即可进入网站。

## 本地一体化验收

```powershell
cd D:\projects\SupplyGuard-Agent
.\.venv\Scripts\python.exe scripts\seed_demo_cases.py
cd frontend
npm run build
cd ..
$env:PYTHONPATH='D:\projects\SupplyGuard-Agent\backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

访问：`http://127.0.0.1:8001/`

检查：

- `/api/health`
- `/api/system/provider-status`
- `/demo`
- `/tasks`
- `/tasks/{task_id}`
- `/api/diligence/tasks/{task_id}/report.pdf`

## Render 部署步骤

1. 将代码推送到 GitHub。
2. 在 Render 创建 Blueprint 或 Web Service。
3. 选择本仓库，使用根目录 `Dockerfile`。
4. `render.yaml` 已设置 Docker 部署、health check 和 `$PORT` 启动。
5. 在 Render Environment Variables 中设置 Secret。
6. 部署完成后访问 Render 根路径。

## 必填 Secret

不要写入代码、README、前端或 `render.yaml` 明文字段。

```env
TENCENTCLOUD_SECRET_ID=<Render Secret>
TENCENTCLOUD_SECRET_KEY=<Render Secret>
DEEPSEEK_API_KEY=<Render Secret>
```

## 推荐非 Secret 环境变量

```env
DEPLOYMENT_MODE=demo
DEMO_MODE_ENABLED=true
CACHE_DEMO_TASKS=true
ENABLE_REAL_QUERY=true
MODEL_MODE=llm
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
WEB_SEARCH_PROVIDER=real
WEB_SEARCH_API=tencent
TENCENT_WSA_PROVIDER=real
TENCENT_WSA_ENDPOINT=https://wsa.tencentcloudapi.com
TENCENT_WSA_ACTION=SearchPro
TENCENT_WSA_VERSION=2025-05-08
REAL_QUERY_DAILY_LIMIT=20
REAL_QUERY_CACHE_DAYS=7
LLM_FALLBACK_TO_MOCK=true
PROVIDER_FALLBACK_TO_MOCK=true
```

## 安全检查

- `.env` 和 `backend/.env` 必须被 `.gitignore` 忽略。
- `/api/health` 只显示 masked/configured 状态。
- 真实查询失败时允许 fallback，但必须在事件中记录原因。
- SQLite 适合演示；生产建议换 PostgreSQL 并加鉴权。

## 常见问题

- 首页 404：确认 `npm run build` 已在 Docker build 阶段完成。
- PDF 中文乱码：Dockerfile 已安装 `fonts-noto-cjk`；本地 Windows 使用 Microsoft YaHei。
- Real Query 按钮置灰：检查 `ENABLE_REAL_QUERY`、腾讯云 Secret 和 `WEB_SEARCH_PROVIDER=real`。
- 真实查询次数耗尽：调整 `REAL_QUERY_DAILY_LIMIT` 或使用缓存 Demo。
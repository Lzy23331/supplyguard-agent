# Deployment Guide

推荐部署方式：FastAPI 同时服务 API 与前端 `dist`，减少跨域和双平台配置。

## 本地一键演示

```powershell
cd D:\projects\SupplyGuard-Agent
.\.venv\Scripts\python.exe scripts\seed_demo_cases.py
cd frontend
npm run build
cd ..\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问 `http://127.0.0.1:8000`。

## Docker Compose

```powershell
cd D:\projects\SupplyGuard-Agent
docker compose up --build
```

访问 `http://127.0.0.1:8000`。

## Render/Railway/Fly.io/云服务器

1. 使用仓库根目录 Dockerfile 构建镜像。
2. 暴露端口 `8000`。
3. 设置环境变量，默认演示建议：
   - `DEPLOYMENT_MODE=demo`
   - `ENABLE_REAL_QUERY=false`
   - `ENABLE_LLM_REPORT_POLISH=true`
   - `LLM_FALLBACK_TO_MOCK=true`
4. 如需 Real Query Mode，在平台 Secret 中配置：
   - `TENCENTCLOUD_SECRET_ID`
   - `TENCENTCLOUD_SECRET_KEY`
   - `OPENAI_BASE_URL`
   - `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY`
   - `OPENAI_MODEL`
5. 部署后访问 `/api/health` 和 `/api/system/provider-status` 检查服务状态。

SQLite 可用于演示部署；生产环境建议迁移到 PostgreSQL 并增加鉴权、审计和访问控制。

# SupplyGuard Agent

SupplyGuard Agent is a portfolio-grade supplier onboarding due diligence system. It demonstrates how a procurement or compliance team can use an agent workflow to collect evidence, retrieve policy knowledge, score risks and generate a review-ready report.

## Project Positioning

This project is designed for interviews and engineering demos. It uses reproducible mock business data instead of sensitive real company data, while keeping the architecture close to a production workflow:

- FastAPI backend with SQLite persistence.
- Five-agent orchestration pipeline.
- Tool calling for search, policy retrieval, risk rules, evidence storage and report generation.
- React/Vite frontend for task creation, execution trace, risk portrait and report review.
- Default deterministic mock mode with optional OpenAI-compatible LLM mode.

## Core Features

- Create supplier due diligence tasks.
- Run Intake, Evidence Collector, Compliance Risk, Business Risk and Report agents.
- Retrieve policy snippets from a local RAG-style knowledge base.
- Generate low, medium and high risk outcomes from stable sample suppliers.
- Store agent events, evidence, assessments, reports and human review records.
- View the full execution timeline and Markdown report in the frontend.

## Tech Stack

- Backend: Python, FastAPI, Pydantic, SQLite, pytest.
- Agent engineering: orchestrator, structured context, tool interfaces, policy RAG, rules engine.
- Frontend: React, TypeScript, Vite, lucide-react, marked.
- Data: local JSON samples and Markdown policy knowledge base.

## Quick Start

Recommended on Windows:

```powershell
cd "D:\projects\SupplyGuard Agent"
.\scripts\start-backend.ps1
```

Open a second terminal:

```powershell
cd "D:\projects\SupplyGuard Agent"
.\scripts\start-frontend.ps1
```

Backend manually:

```powershell
cd "D:\projects\SupplyGuard Agent\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Frontend manually, if Node.js/npm is already on PATH:

```powershell
cd "D:\projects\SupplyGuard Agent\frontend"
npm install
npm run dev
```

Open `http://127.0.0.1:5173` and choose a low, medium or high risk sample supplier.

## API Examples

Create a task:

```powershell
Invoke-RestMethod -Method Post "http://127.0.0.1:8000/api/diligence/tasks" `
  -ContentType "application/json" `
  -Body '{"supplier":{"name":"GreenFlow Components Ltd.","website":"https://greenflow.example.com","industry":"Industrial components","region":"Singapore","annual_spend":180000,"cooperation_type":"standard parts supplier","sample_key":"low"}}'
```

Read events:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/{task_id}/events"
```

Read report:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/diligence/tasks/{task_id}/report"
```

## Sample Suppliers

- Low risk: `GreenFlow Components Ltd.` has complete registration and no material negative signal.
- Medium risk: `Northbridge Packaging Co.` has settled litigation and delivery delay signals.
- High risk: `Redstone Metals Trading` has sanction proximity and bribery allegation signals.

## Model Modes

Default mode is deterministic and requires no API key:

```powershell
$env:MODEL_MODE="mock"
```

LLM mode is OpenAI-compatible:

```powershell
$env:MODEL_MODE="llm"
$env:OPENAI_BASE_URL="https://api.openai.com/v1"
$env:OPENAI_API_KEY="..."
$env:OPENAI_MODEL="gpt-4o-mini"
```

The current v1 keeps LLM usage optional so the demo always runs without network access.

## Interview Highlights

- Shows domain understanding of supplier onboarding, procurement risk and compliance review.
- Uses agent events as observable execution traces, not hidden chain behavior.
- Combines deterministic rules and RAG snippets so the demo is stable and explainable.
- Keeps a clear extension point for real search APIs, queues, WebSocket/SSE streaming and LLM summarization.

## Future Extensions

- Replace mock search with real registry, sanctions and adverse media APIs.
- Add background task queue and streaming event transport.
- Add document upload for supplier certificates and contracts.
- Add evaluation dashboards for policy hit rate and risk rating consistency.
- Add authentication, role-based approvals and audit exports.

# ⚡ QuickFixer: AI-Powered Enterprise IT Support & Intelligent Issue Resolution Platform

> **"Identify. Diagnose. Resolve."**

An enterprise-grade, ITIL-compliant IT Service Desk & Intelligent Issue Resolution Platform. QuickFixer replaces legacy UI layers with a modern, responsive **React 18** Single Page Application powered by a high-performance **FastAPI** REST API adapter, while strictly preserving the autonomous **LangGraph (12-Node StateGraph Orchestrator)**, **FAISS Vector Database (`IndexFlatIP`)**, **SentenceTransformers (`all-MiniLM-L6-v2`)**, **Google Gemini (`gemini-2.0-flash`)**, and **SQLite database (`data/tickets.db`)**.

[![Tests](https://img.shields.io/badge/tests-131%20passed-brightgreen.svg)](tests/)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%2018%20%7C%20Vite-61DAFB.svg)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🌟 Key Capabilities & Target Architecture

```
+--------------------------------------------------------------+
|              React 18 Frontend (Vite, SPA)                  |
|   - Enterprise Dark Theme (#0B1020, #111827, #172033)        |
|   - QuickFixer Branding: "Identify. Diagnose. Resolve."       |
|   - Employee Dashboard & AI Chat (Markdown, Runbook Sources) |
|   - Technician Workspace (Queue Dispatch, Notes, Status)     |
|   - Admin Dashboard (KPIs, Recharts Analytics, User Admin)   |
|   - Knowledge Base Hub (Upload, FAISS Reindex, Vector Test)   |
+------------------------------+-------------------------------+
                               | REST API (Axios / Bearer JWT)
                               v
+--------------------------------------------------------------+
|               FastAPI REST API Adapter Layer                 |
|   - /api/auth: Login, Logout, Current User Profile           |
|   - /api/chat: Stateful Query, History, Citations, Escalate  |
|   - /api/tickets: Scoped Listing, Create, Status, Notes      |
|   - /api/dashboard: Real-Time Stats, Metrics, Distributions  |
|   - /api/admin: User Lifecycle CRUD, Audit Logs, Security    |
|   - /api/knowledge: Document list, Upload, FAISS Re-indexing |
|   - /api/system: Diagnostics Health, Gemini Configuration    |
+------------------------------+-------------------------------+
                               | Native In-Process Python Calls
                               v
+--------------------------------------------------------------+
|              Preserved Python Business Services              |
|   - SupportTriageAgent, DomainClassifier                     |
|   - KnowledgeRetriever, FAISS Vector Store, Embeddings       |
|   - GeminiClient, OfflineDiagnosticEngine Fallback           |
|   - DatabaseManager (SQLite data/tickets.db & checkpoints.db)|
|   - AuthManager, PasswordManager (Bcrypt rounds: 12)         |
+--------------------------------------------------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version / Specification |
| :--- | :--- | :--- |
| **Frontend Framework** | React.js / Vite | `React 19` / `Vite 8` SPA with responsive flex/grid |
| **Routing** | React Router | `react-router-dom 7` with Role-Based Protected Routes |
| **Icons & Visuals** | Lucide React | `lucide-react` enterprise iconography |
| **Analytics Charts** | Recharts | Recharts BarChart & PieChart for IT desk metrics |
| **Markdown & Formatting** | React Markdown | `react-markdown` + `remark-gfm` with code blocks |
| **API Client** | Axios | Interceptors with Bearer JWT & 401 handling |
| **REST API Server** | FastAPI / Uvicorn | `FastAPI 0.162`, `uvicorn`, `pyjwt`, `python-multipart` |
| **Agent Orchestration** | LangGraph | 12-Node StateGraph with SQLite checkpointing |
| **RAG & Vector Store** | FAISS | `faiss-cpu` (IndexFlatIP unit-normalized cosine) |
| **Embeddings** | SentenceTransformers | `all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| **LLM Provider** | Google Gemini | `gemini-2.0-flash` with offline heuristic fallback |
| **Database** | SQLite | `data/tickets.db` & `data/checkpoints.db` |
| **Testing** | Pytest | `pytest 9.2.0` with **131 automated tests (100% pass rate)** |

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Python 3.12 verified)
- Node.js 18+ (Node v22 verified) & npm

### 2. Backend Startup (FastAPI)
Activate the Python virtual environment and start Uvicorn:
```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Start FastAPI backend
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI REST API will be running at:
- **API Base:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **Alternative ReDoc:** `http://127.0.0.1:8000/redoc`

### 3. Frontend Startup (React Vite)
In a separate terminal, run the Vite development server:
```powershell
cd frontend
npm install
npm run dev
```
The QuickFixer React application will open at:
- **Web App:** `http://localhost:5173`

> **Note:** Vite automatically proxies `/api` calls directly to `http://127.0.0.1:8000`.
> In production or single-port mode, running `npm run build` inside `frontend/` builds static assets to `frontend/dist`, which FastAPI automatically serves directly at `http://127.0.0.1:8000/`.

---

## 👥 Seeded Corporate Test Accounts

| Role | Username | Corporate Email | Password | Access Scope |
| :--- | :--- | :--- | :--- | :--- |
| **👑 Admin** | `admin` | `admin@company.com` | `ApexAdmin2026!` | Global oversight, all tickets, user management, KB upload/reindex, audit logs |
| **🛠️ Technician** | `tech_sarah` | `sarah.connor@example.com` | `Password123!` | Network queue (`NetOps`), assigned tickets, status lifecycle, AI summary draft |
| **🛠️ Technician** | `tech_mike` | `mike.ross@company.com` | `Password123!` | Hardware queue (`Deskside`), assigned tickets, status lifecycle |
| **👤 Employee** | `emp_david` | `dmiller@company.com` | `Password123!` | Employee portal, personal tickets only, AI chat troubleshooting, ticket submission |
| **👤 Employee** | `emp_alice` | `alice@company.com` | `Password123!` | Employee portal, personal tickets only, AI chat troubleshooting |

---

## 🛡️ Critical AI Guardrails & Verification

QuickFixer enforces strict domain classification and retrieval safety:

1. **Out-of-Scope Rejection**:
   - Query: `"pm of india"` or general trivia.
   - Behavior: Immediately intercepted and politely rejected with:
     > *"Your question does not appear to be related to IT support or a technical system issue. Please describe your IT problem again, and I'll help you troubleshoot it."*

2. **Relevant Technical Troubleshooting**:
   - Query: `"My system suddenly froze and switched off."`
   - Behavior: Correctly classified under hardware shutdown/crash; asks diagnostic questions regarding thermal throttling, power supply, and Event Viewer logs. Never returns printer or VPN instructions.

3. **Login & MFA Troubleshooting**:
   - Query: `"I cannot log in to my company account."`
   - Behavior: Delivers step-by-step account authentication and Microsoft Entra ID / MFA reset instructions.

---

## 🧪 Automated Test Suite

Run all 131 tests covering auth, database, domain classification, RAG, agentic graph, and FastAPI endpoints:
```powershell
.venv\Scripts\python -m pytest -v
```
All **131 tests pass with 100% success rate**.

---

## 🔄 Rollback Option (Streamlit)
The original Streamlit application remains intact at `app.py` for rollback or comparison:
```powershell
.venv\Scripts\streamlit run app.py
```

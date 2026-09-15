# Multi-Agent Equity Research Terminal

A full-stack equity research dashboard that pulls real-time financial metrics and news, runs parallel multi-agent analysis via LangGraph and Google Gemini, validates the output with deterministic guardrails, and caches reports in Neon PostgreSQL.

[![CI Pipeline](https://github.com/zain-syed01/multi_llm_stock_analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/zain-syed01/multi_llm_stock_analysis/actions)
[![Live Demo](https://img.shields.io/badge/Vercel-Live%20Demo-black?logo=vercel)](https://multi-llm-stock-analysis-git-main-zain-syed01s-projects.vercel.app)
[![API Docs](https://img.shields.io/badge/Render-FastAPI%20Docs-46E3B7?logo=render)](https://equity-research-api-jsnr.onrender.com/docs)

---

## Demos

### Live Analysis Run (~30s)
Generates an investment memo from scratch: pulls data via Yahoo Finance, indexes news into ChromaDB, executes parallel analyst nodes, runs the guardrail audit, and stores the dossier in PostgreSQL.

![Live Analysis Demo](assets/live-run-demo.gif)

### Sub-50ms Cache Hit (<24h TTL)
Repeating a ticker lookup pulls directly from Neon PostgreSQL, bypassing LLM inference entirely to protect API quotas.

![Cache Hit Demo](assets/cached-run-demo.gif)

---

## How It Works

┌─────────────────────────────────┐
                  │    Next.js Terminal Frontend    │
                  └────────────────┬────────────────┘
                                   │ POST /api/v1/research/{ticker}
                                   ▼
                  ┌─────────────────────────────────┐
                  │         FastAPI Backend         │
                  └────────┬───────────────┬────────┘
         Cache Hit (<24h)  │               │ Cache Miss
                           ▼               ▼
                ┌──────────────────┐  ┌───────────────────────────┐
                │ Neon PostgreSQL  │  │ Ingester (yfinance + HTTP)│
                └──────────────────┘  └─────────────┬─────────────┘
                                                    │
                               ┌────────────────────┴────────────────────┐
                               ▼                                         ▼
                    ┌─────────────────────┐                   ┌─────────────────────┐
                    │  Financial Metrics  │                   │ ChromaDB Vector DB  │
                    │ (P/E, Margins, FCF) │                   │  (Embedded News)    │
                    └──────────┬──────────┘                   └──────────┬──────────┘
                               │                                         │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                                   ┌─────────────────────────────────┐
                                   │     LangGraph State Graph       │
                                   │                                 │
                                   │  ┌───────────────────────────┐  │
                                   ├─►│    fundamental_analyst    ├──┤
                                   │  └───────────────────────────┘  │
                                   │                                 │
                                   │  ┌───────────────────────────┐  │
                                   ├─►│     sentiment_analyst     ├──┤
                                   │  │     (ChromaDB context)    │  │
                                   │  └───────────────────────────┘  │
                                   │                │                │
                                   │                ▼                │
                                   │  ┌───────────────────────────┐  │
                                   │  │       chief_arbiter       │  │
                                   │  │    (Synthesizes Memo)     │  │
                                   │  └─────────────┬─────────────┘  │
                                   │                ▼                │
                                   │  ┌───────────────────────────┐  │
                                   │  │    evaluator_guardrail    │  │
                                   │  │   (Deterministic Audit)   │  │
                                   │  └─────────────┬─────────────┘  │
                                   └────────────────┼────────────────┘
                                                    │
                                                    ▼
                                         Persist to Neon Cache







---

## Core Implementation Details

* **Parallel Node Execution:** In `graph.py`, `fundamental_analyst` and `sentiment_analyst` branch out concurrently from `START` using LangGraph. Running them in parallel minimizes report generation turnaround.
* **Semantic News Ingestion:** Yahoo Finance news articles are sanitized, hashed with SHA-256 to avoid duplicate entries, and embedded inside a persistent local ChromaDB collection (`store.py`).
* **Deterministic Guardrail Node:** Before the final memo is delivered or saved to the database, `evaluator_guardrail` runs verification checks on the text. It confirms the presence of explicit ratings (`STRONG BUY`, `BUY`, `HOLD`, `SELL`) and verifies that valuation metrics (P/E, margins) are cited.
* **24-Hour PostgreSQL Cache:** Tickers queried within 24 hours are served directly from Neon (`database.py`, `main.py`), cutting response times and preventing redundant Gemini API calls.
* **Resilient Data Scraping:** The `yfinance` scraper uses a custom browser session header and falls back to `ticker.fast_info` if Yahoo Finance encounters authentication crumb challenges on datacenter IP addresses.

---

## Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend & APIs** | FastAPI, SQLModel, Uvicorn, Pydantic v2 |
| **Orchestration & AI** | LangGraph, LangChain, Google Gemini (`gemini-3.5-flash-lite`) |
| **Databases** | Neon PostgreSQL (Managed Cache), ChromaDB (Vector Store) |
| **Frontend UI** | Next.js, TypeScript, Tailwind CSS |
| **DevOps & Infra** | Docker, Docker Compose, GitHub Actions, Render, Vercel |

---

## Project Structure

.
├── .github/workflows/
│   └── ci.yml             # GitHub Actions: Automated Pytest & Docker build checks
├── assets/                # Demo GIFs for documentation
├── chroma_data/           # Persistent volume directory for ChromaDB embeddings
├── frontend/
│   ├── src/app/
│   │   ├── layout.tsx     # Next.js global layout
│   │   └── page.tsx       # Real-time investment terminal interface
│   ├── Dockerfile         # Standalone multi-stage production Docker build
│   └── package.json
├── database.py            # SQLModel schema and database engine (Neon / SQLite)
├── docker-compose.yml     # Multi-container orchestration (Backend + Frontend)
├── Dockerfile             # Production Python 3.12 slim backend container
├── graph.py               # LangGraph state machine, nodes, and parallel edges
├── ingest.py              # Financial data scraping and resilient parsing layer
├── main.py                # FastAPI endpoints, CORS setup, and caching routes
├── requirements.txt       # Python dependency specifications
└── store.py               # ChromaDB collection management and semantic retrieval


---

## Local Setup & Development

### 1. Prerequisites
* Docker & Docker Compose installed
* Python 3.12+ (for manual local execution)
* Node.js 20+ (for manual frontend development)
* A Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))
* A PostgreSQL database URL ([Neon.tech](https://neon.tech/) or local SQLite fallback)

### 2. Clone & Configure Environment
```bash
git clone [https://github.com/zain-syed01/multi_llm_stock_analysis.git](https://github.com/zain-syed01/multi_llm_stock_analysis.git)
cd multi_llm_stock_analysis
Create a .env file in the root directory:

Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require
Running with Docker Compose (Recommended)
To build and run both the FastAPI backend and Next.js frontend in isolated containers:

Bash
docker compose up --build
Frontend Terminal: http://localhost:3000

FastAPI Docs: http://localhost:8000/docs

Chroma Data: Automatically persisted to ./chroma_data on the host machine.

Running Manually
Backend Setup
Bash
# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn main:app --reload --port 8000
Frontend Setup
Bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
API Reference
Health Check
GET /api/v1/health

JSON
{
  "status": "online"
}
Analyze Stock Ticker
POST /api/v1/research/{ticker}

Response (Sample Live or Cache Output):

JSON
{
  "source": "live_generation",
  "ticker": "NVDA",
  "current_price": 118.25,
  "trailing_pe": 45.32,
  "created_at": "2026-09-15T11:15:30.123456Z",
  "passed_guardrail": true,
  "audit_notes": "Passed audit: explicit rating and core metrics verified.",
  "final_report": "# Executive Investment Dossier: NVIDIA Corporation (NVDA)\n..."
}
Continuous Integration & Testing
The repository runs an automated CI pipeline on every push via .github/workflows/ci.yml:

Unit Testing: Runs pytest test suites verifying API responses and data handling.

Container Verification: Validates Docker builds for clean deployments.

To run tests locally:

Bash
pytest

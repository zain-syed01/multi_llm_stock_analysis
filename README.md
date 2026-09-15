# Multi-Agent Equity Research Terminal

A containerized, multi-agent equity analysis platform that synthesizes real-time market data, conducts semantic news retrieval, and generates audited investment dossiers using Google Gemini, LangGraph, ChromaDB, and Neon PostgreSQL.

[![CI Pipeline](https://github.com/zain-syed01/multi_llm_stock_analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/zain-syed01/multi_llm_stock_analysis/actions)
[![Live Demo](https://img.shields.io/badge/Vercel-Live%20Demo-black?logo=vercel)](https://YOUR_VERCEL_APP_URL_HERE.vercel.app)
[![API Status](https://img.shields.io/badge/Render-API%20Online-46E3B7?logo=render)](https://YOUR_RENDER_URL_HERE.onrender.com/docs)

---

## Interactive Demos

### 1. Live Multi-Agent Synthesis Pipeline
![Live Run Demo](./assets/live-run-demo.gif)
*Live run: Ingests market metrics and news, indexes articles into ChromaDB, executes parallel LangGraph agents, runs deterministic guardrails, and saves to Neon PostgreSQL.*

### 2. Sub-50ms Tier-1 Cache Invalidation (24h TTL)
![Cached Run Demo](./assets/cached-run-demo.gif)
*Neon PostgreSQL query cache: Instant sub-50ms retrieval for repeated ticker lookups within the 24-hour evaluation window.*

---

## System Architecture

```text
                      ┌────────────────────────────────────────┐
                      │        User / Next.js Terminal         │
                      └───────────────────┬────────────────────┘
                                          │ POST /api/v1/research/{ticker}
                                          ▼
                      ┌────────────────────────────────────────┐
                      │           FastAPI Gateway              │
                      └─────┬────────────────────────────┬─────┘
                            │ Cache Hit (<24 hrs)        │ Cache Miss
                            ▼                            ▼
                 ┌────────────────────┐       ┌────────────────────────┐
                 │  Neon PostgreSQL   │       │   Ingestion Engine     │
                 │  (AnalysisRecord)  │       │ (yfinance + Fallbacks) │
                 └────────────────────┘       └──────────┬─────────────┘
                                                         │
                                        ┌────────────────┴────────────────┐
                                        ▼                                 ▼
                             ┌─────────────────────┐           ┌─────────────────────┐
                             │ Financial Metrics   │           │ Vector Store (RAG)  │
                             │ (P/E, FCF, Margins) │           │ ChromaDB Persistent │
                             └──────────┬──────────┘           └──────────┬──────────┘
                                        │                                 │
                                        └────────────────┬────────────────┘
                                                         ▼
                                 ┌───────────────────────────────────────────────┐
                                 │       LangGraph Multi-Agent Orchestrator      │
                                 │                                               │
                                 │        ┌─────────────────────────────┐        │
                                 │   ┌───►│    fundamental_analyst      ├───┐    │
                                 │   │    │  (Valuation & Balance Sheet)│   │    │
                                 │   │    └─────────────────────────────┘   │    │
                                 │ START                                    ├──► │
                                 │   │    ┌─────────────────────────────┐   │    │
                                 │   └───►│      sentiment_analyst      ├───┘    │
                                 │        │   (ChromaDB Semantic RAG)   │        │
                                 │        └─────────────────────────────┘        │
                                 │                       │                       │
                                 │                       ▼                       │
                                 │        ┌─────────────────────────────┐        │
                                 │        │        chief_arbiter        │        │
                                 │        │    (Dossier & Conviction)   │        │
                                 │        └──────────────┬──────────────┘        │
                                 │                       ▼                       │
                                 │        ┌─────────────────────────────┐        │
                                 │        │     evaluator_guardrail     │        │
                                 │        │(Deterministic Quality Audit)│        │
                                 │        └──────────────┬──────────────┘        │
                                 │                       ▼                       │
                                 │                      END                      │
                                 └───────────────────────┬───────────────────────┘
                                                         │ Persist Output
                                                         ▼
                                              ┌────────────────────┐
                                              │  Neon PostgreSQL   │
                                              └────────────────────┘




Key Technical Highlights
Concurrent Multi-Agent Fan-Out: Leverages LangGraph to parallelize execution across the fundamental_analyst (quantitative ratios) and sentiment_analyst (ChromaDB semantic search) nodes, minimizing end-to-end LLM inference latency.

Semantic RAG Ingestion: Articles fetched through Yahoo Finance are deduplicated, embedded, and indexed inside a persistent local ChromaDB instance with deterministic SHA-256 metadata hashing.

Deterministic Guardrail Agent: The evaluator_guardrail node inspects final synthesized dossiers using deterministic rules (validating explicit rating presence: STRONG BUY, BUY, HOLD, SELL, and numerical metric references) before serialization.

Tiered 24-Hour Cache: Built on SQLModel and Neon PostgreSQL (AnalysisRecord). Queries are checked against the database; valid dossiers (<24 hours old) return instantly, shielding the external APIs from redundant calls and quota limits.

Resilient Data Ingestion: Features a hardened scraping layer using custom user-agent sessions, fallback fast-info extraction, and graceful degradation against cloud IP rate limits.

Tech Stack
Layer	Technologies
Backend & APIs	FastAPI, SQLModel, Uvicorn, Pydantic v2
Orchestration & AI	LangGraph, LangChain, Google Gemini (gemini-3.5-flash-lite)
Databases	Neon PostgreSQL (Managed OLTP/Cache), ChromaDB (Vector Store)
Frontend UI	Next.js 15, TypeScript, Tailwind CSS, Lucide React, React Markdown
DevOps & Infra	Docker, Docker Compose, GitHub Actions (Pytest + Buildx), Render, Vercel
Project Structure
Plaintext
.
├── .github/workflows/
│   └── ci.yml             # GitHub Actions: Automated Pytest & Docker build checks
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
Local Setup & Development
1. Prerequisites
Docker & Docker Compose installed

Python 3.12+ (for manual local execution)

Node.js 20+ (for manual frontend development)

A Google Gemini API Key (Google AI Studio)

A PostgreSQL database URL (Neon.tech or local PostgreSQL)

2. Clone & Configure Environment
Bash
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

Container Verification: Validates Docker Buildx compilation for clean deployments.

To run tests locally:

Bash
pytest
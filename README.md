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

## Features

* **Parallel Multi-Agent Workflow:** Runs quantitative fundamental metrics evaluation and sentiment news retrieval concurrently using LangGraph to cut report generation latency in half.
* **Semantic News Ingestion & RAG:** Scrapes real-time market updates, deduplicates articles using SHA-256 hashes, and indexes embeddings into ChromaDB for contextual retrieval.
* **Deterministic Guardrail Audit:** Programmatically audits generated dossiers to verify explicit investment ratings (STRONG BUY, BUY, HOLD, SELL) and citations of valuation metrics before response delivery.
* **Sub-50ms 24-Hour Cache:** Caches complete equity dossiers in Neon PostgreSQL with a 24-hour expiration window to prevent redundant LLM token consumption.
* **Resilient Market Scraping:** Hardens Yahoo Finance data ingestion with custom browser session headers and fast-info extraction fallbacks to handle datacenter IP rate limits.

---

## Tech Stack

* **Frontend:** Next.js 15, TypeScript, Tailwind CSS, Lucide React
* **Backend API:** FastAPI, Uvicorn, SQLModel, Pydantic v2
* **AI & Orchestration:** LangGraph, LangChain, Google Gemini (`gemini-3.5-flash-lite`)
* **Vector Database:** ChromaDB (Embedded Persistent Client)
* **Relational Database:** PostgreSQL (Neon Serverless)
* **Deployment Platforms:** Vercel (UI), Render (API)

---

## System Architecture

* **Frontend Layer:** Hosted on Vercel, providing an interactive terminal interface, dynamic API status monitoring, and real-time report rendering.
* **API Gateway:** Hosted on Render using a Docker container, providing FastAPI routes for research generation and cache verification.
* **Agent Engine:** Orchestrated using LangGraph state graphs with parallel branching for fundamental and sentiment analysts feeding into a synthesis arbiter.
* **Database Layer:**
  * Relational cache and audit logs managed via Neon PostgreSQL.
  * Semantic news embeddings stored locally via persistent ChromaDB storage.

---

## Local Setup & Installation

### Prerequisites
* Python 3.12+
* Node.js 20+
* Docker & Docker Compose (optional, for containerized run)
* A Google Gemini API Key
* A PostgreSQL Database connection string (Neon or local)

### 1. Clone Repository
```bash
git clone [https://github.com/zain-syed01/multi_llm_stock_analysis.git](https://github.com/zain-syed01/multi_llm_stock_analysis.git)
cd multi_llm_stock_analysis


### 2. Environment Variables
Create a `.env` file in the root directory:

GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@ep-xyz.neon.tech/neondb?sslmode=require

### 3. Run with Docker Compose (Recommended)
```bash
docker compose up --build


* Frontend Terminal: http://localhost:3000

* FastAPI Docs: http://localhost:8000/docs


### 4. Run Manually
Start the FastAPI backend:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

In a separate terminal, start the Next.js frontend:
cd frontend
npm install
npm run dev

### Project Structure
.
├── .github/workflows/
│   └── ci.yml             # GitHub Actions: Pytest & Docker build checks
├── assets/                # Demo GIFs for documentation
├── chroma_data/           # Persistent ChromaDB storage
├── frontend/              # Next.js terminal frontend
│   ├── src/app/
│   │   ├── layout.tsx     # Global layout
│   │   └── page.tsx       # Search dashboard & report viewer
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

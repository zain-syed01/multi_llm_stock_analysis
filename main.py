from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from contextlib import asynccontextmanager

from database import create_db_and_tables, get_session, AnalysisRecord
from ingest import fetch_ticker_data
from store import store_news
from graph import research_graph, ResearchState

@asynccontextmanager

async def lifespan(app: FastAPI):
    # running on startup
    create_db_and_tables()

    yield


app = FastAPI(
    title="Multi Agent Stock Research",
    description="Multi-agent financial research system powered by LangGraph, ChromaDB, and Google Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "online"}



@app.post("/api/v1/research/{ticker}")

def analyze_ticker(ticker: str, session: Session = Depends(get_session)):
    symbol = ticker.upper().strip()


    #Checking database for existing stock anaylsis within the last 24 hours

    statement = (
        select(AnalysisRecord)
        .where(AnalysisRecord.ticker == symbol)
        .order_by(AnalysisRecord.created_at.desc())
    )
    cached_record = session.exec(statement).first()


    if cached_record:
        created = cached_record.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)


        if datetime.now(timezone.utc) - created < timedelta(hours=24):
            return {
                "source": "cache",
                "ticker": cached_record.ticker,
                "current_price": cached_record.current_price,
                "trailing_pe": cached_record.pe_ratio,
                "created_at": cached_record.created_at,
                "passed_guardrail": cached_record.passed_guardrail,
                "audit_notes": cached_record.audit_notes,
                "final_report": cached_record.final_report,
            }


    payload = fetch_ticker_data(symbol)

    if not payload.metrics.current_price:
        raise HTTPException(status_code=404,detail=f"No market data found for ticker '{symbol}'.")

    # Vectorize the news in ChromaDB
    store_news(symbol, payload.news)


    # Run the multi agent workflow

    initial_state: ResearchState = {
        "ticker": symbol,
        "metrics": payload.metrics.model_dump(),
        "fundamental_analysis": None,
        "sentiment_analysis": None,
        "final_report": None,
        "passed_guardrail": None,
        "audit_notes": None,
    }


    result = research_graph.invoke(initial_state)


    # Put the record into Neon Database

    record = AnalysisRecord(
        ticker=symbol,
        current_price=payload.metrics.current_price,
        pe_ratio=payload.metrics.trailing_pe,
        final_report=result.get("final_report", ""),
        passed_guardrail=bool(result.get("passed_guardrail")),
        audit_notes=result.get("audit_notes"),
    )

    session.add(record)
    session.commit()
    session.refresh(record)



    return {
        "source": "live_generation",
        "ticker": record.ticker,
        "current_price": record.current_price,
        "trailing_pe": record.pe_ratio,
        "created_at": record.created_at,
        "passed_guardrail": record.passed_guardrail,
        "audit_notes": record.audit_notes,
        "final_report": record.final_report,
    }



    
import os
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import SQLModel, Field, create_engine, Session

load_dotenv()

class AnalysisRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    final_report: str
    passed_guardrail: bool
    audit_notes: Optional[str] = None

# Grab DB URL from .env, fall back on sqlite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./research_cache.db")


# need multiple worker threads
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


    
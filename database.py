from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select


class AnalysisRecord(SQLModel,table=True):
    
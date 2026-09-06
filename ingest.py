from typing import List, Optional
import yfinance as yf
from pydantic import BaseModel, Field



class news_article(BaseModel):
    title: str
    publisher: str
    link: str
    summary: Optional[str] = None



class financial_metrics(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    profit_margins: Optional[float] = None
    free_cashflow: Optional[int] = None



class ticker_payload(BaseModel):
    metrics: financial_metrics
    news: List[news_article] = Field(default_factory=list)



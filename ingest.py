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


def fetch_ticker_data(symbol: str) -> ticker_payload:
    ticker = yf.Ticker(symbol)

    info = ticker.info or {}

    metrics = financial_metrics(
        ticker=symbol.upper(),
        current_price=info.get("currentPrice") or info.get("regularMarketPrice"),
        trailing_pe=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        peg_ratio=info.get("pegRatio"),
        debt_to_equity=info.get("debtToEquity"),
        profit_margins=info.get("profitMargins"),
        free_cashflow=info.get("freeCashflow"),
    )

    # Extract and clean up the news articles
    raw_news = ticker.news or []
    cleaned_news = []

    for item in raw_news[:5]:
        # Have to access content to get the other details
        content = item.get("content") or {}
        provider = content.get("provider") or {}
        publisher_name = provider.get("displayName") or item.get("publisher") or "Unknown"
        click_url = content.get("clickThroughUrl") or {}
        link_url = click_url.get("url") or item.get("link") or ""
        
        
        cleaned_news.append(
            news_article(
                title=content.get("title", "No title"),
                publisher=publisher_name,
                link=link_url,
                summary = content.get("summary") or content.get("title", "No title")
            )
        )

    return ticker_payload(metrics=metrics,news=cleaned_news)



if __name__ == "__main__":

    result = fetch_ticker_data("NVDA")
    print("=== Extracted Metrics ===")
    print(result.metrics.model_dump_json(indent=2))
    print(f"\n=== Extracted {len(result.news)} News Articles ===")
    for idx, article in enumerate(result.news, 1):
        print(f"{idx}. [{article.publisher}] {article.title}")
        


    

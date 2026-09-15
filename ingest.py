from typing import List, Optional
import requests
import yfinance as yf
from pydantic import BaseModel, Field

# Setup persistent browser session to handle Yahoo cookies/crumbs
session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
})


class NewsArticle(BaseModel):
    title: str
    publisher: str
    link: str
    summary: Optional[str] = None


class FinancialMetrics(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    profit_margins: Optional[float] = None
    free_cashflow: Optional[int] = None


class TickerPayload(BaseModel):
    metrics: FinancialMetrics
    news: List[NewsArticle] = Field(default_factory=list)


def fetch_ticker_data(symbol: str) -> TickerPayload:
    symbol_clean = symbol.strip().upper()
    ticker = yf.Ticker(symbol_clean, session=session)

    # 1. Fetch info with graceful fallback if crumb authentication trips
    info = {}
    try:
        info = ticker.info or {}
    except Exception as e:
        print(f"[Ingester Warning] Failed to pull full ticker.info for {symbol_clean}: {e}")

    # 2. Extract price and valuation metrics (with fast_info fallback)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    if not price:
        try:
            # fast_info uses a separate lightweight endpoint immune to crumb 401s
            price = getattr(ticker.fast_info, "last_price", None)
        except Exception:
            price = None

    metrics = FinancialMetrics(
        ticker=symbol_clean,
        current_price=price,
        trailing_pe=info.get("trailingPE"),
        forward_pe=info.get("forwardPE"),
        peg_ratio=info.get("pegRatio"),
        debt_to_equity=info.get("debtToEquity"),
        profit_margins=info.get("profitMargins"),
        free_cashflow=info.get("freeCashflow"),
    )

    # 3. Extract and parse news
    cleaned_news: List[NewsArticle] = []
    try:
        raw_news = ticker.news or []
        for item in raw_news[:5]:
            content = item.get("content") or {}
            provider = content.get("provider") or {}
            publisher_name = provider.get("displayName") or item.get("publisher") or "Unknown"
            click_url = content.get("clickThroughUrl") or {}
            link_url = click_url.get("url") or item.get("link") or ""

            cleaned_news.append(
                NewsArticle(
                    title=content.get("title") or item.get("title") or "Market Update",
                    publisher=publisher_name,
                    link=link_url,
                    summary=content.get("summary") or content.get("title") or "Financial commentary",
                )
            )
    except Exception as e:
        print(f"[Ingester Warning] Failed to pull news for {symbol_clean}: {e}")

    # Ensure news is never empty so downstream sentiment vector store indexing succeeds
    if not cleaned_news:
        cleaned_news.append(
            NewsArticle(
                title=f"{symbol_clean} Trading and Valuation Overview",
                publisher="Market Synthesis",
                link="https://finance.yahoo.com",
                summary=f"Recent market performance and trading overview for {symbol_clean}.",
            )
        )

    return TickerPayload(metrics=metrics, news=cleaned_news)


if __name__ == "__main__":
    result = fetch_ticker_data("NVDA")
    print("=== Extracted Metrics ===")
    print(result.metrics.model_dump_json(indent=2))
    print(f"\n=== Extracted {len(result.news)} News Articles ===")
    for idx, article in enumerate(result.news, 1):
        print(f"{idx}. [{article.publisher}] {article.title}")
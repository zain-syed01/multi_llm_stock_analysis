from typing import TypedDict, Optional, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from store import query_news

load_dotenv()

# Initialize Gemini model
llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
)

# Making the Shared Graph State
class ResearchState(TypedDict):
    ticker: str
    metrics: Dict[str, Any]
    fundamental_analysis: Optional[str]
    sentiment_analysis: Optional[str]
    final_report: Optional[str]
    passed_guardrail: Optional[bool]
    audit_notes: Optional[str]

# Node 1: Quantitative Fundamental Analyst
def fundamental_analyst(state: ResearchState) -> dict:
    metrics = state["metrics"]
    ticker = state["ticker"]

    prompt = f"""
    You are a Senior Quantitative Equity Analyst. Analyze the financial health of {ticker}:
    - Current Price: ${metrics.get('current_price')}
    - Trailing P/E: {metrics.get('trailing_pe')}
    - Forward P/E: {metrics.get('forward_pe')}
    - PEG Ratio: {metrics.get('peg_ratio')}
    - Debt-to-Equity: {metrics.get('debt_to_equity')}
    - Profit Margins: {metrics.get('profit_margins')}
    - Free Cash Flow: ${metrics.get('free_cashflow')}

    Provide a concise assessment (2-3 paragraphs) highlighting:
    1. Valuation risk (multiples vs growth).
    2. Balance sheet stability (debt vs cash generation).
    3. Bottom-line margin strength.
    """
    response = llm.invoke(prompt)
    return {"fundamental_analysis": response.content}

# 3. Node 2: Sentiment / News Analyst (ChromaDB RAG)
def sentiment_analyst(state: ResearchState) -> dict:
    ticker = state["ticker"]

    # Semantic search against our local vector store
    search_query = f"{ticker} earnings revenue growth partnerships AI risks"
    rag_results = query_news(ticker=ticker, query_text=search_query, n_results=3)

    docs = rag_results.get("documents", [[]])[0]
    context = "\n---\n".join(docs) if docs else "No recent news indexed."

    prompt = f"""
    You are a Market Sentiment & Catalysts Analyst. 
    Review the following retrieved news items for {ticker}:

    {context}

    Provide a concise assessment (2-3 paragraphs) covering:
    1. Current market sentiment and perception.
    2. Key near-term catalysts or risks (deals, regulation, competition).
    """
    response = llm.invoke(prompt)
    return {"sentiment_analysis": response.content}

# 4. Node 3: Chief Investment Officer (Synthesis & Verdict)
def chief_arbiter(state: ResearchState) -> dict:
    ticker = state["ticker"]
    fund_view = state.get("fundamental_analysis", "")
    sent_view = state.get("sentiment_analysis", "")

    prompt = f"""
    You are the Chief Investment Officer. Synthesize the findings from your two analysts on {ticker}:

    [FUNDAMENTAL ANALYSIS]
    {fund_view}

    [SENTIMENT & CATALYST ANALYSIS]
    {sent_view}

    Provide an Executive Investment Dossier containing:
    1. **Recommendation**: (STRONG BUY / BUY / HOLD / SELL)
    2. **Core Investment Thesis**: 3 key supporting points.
    3. **Key Risks & Downside Scenarios**: 2 critical risks.
    """
    response = llm.invoke(prompt)
    return {"final_report": response.content}



# 5. Guardrail Agent (Make sure correct data being accessed)
def evaluator_guardrail(state: ResearchState) -> dict:
    raw_report = state.get("final_report", "")

    # Normalize response.content if returned as a list of text blocks
    if isinstance(raw_report, list):
        report = " ".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw_report
        )
    else:
        report = str(raw_report or "")

    # Deterministic checks
    verdicts = ["STRONG BUY", "BUY", "HOLD", "SELL"]
    has_verdict = any(v in report for v in verdicts)

    # Checking if the right data was used
    report_lower = report.lower()
    mentions_pe = "p/e" in report_lower or "pe ratio" in report_lower
    mentions_margin = "margin" in report_lower

    passed = has_verdict and (mentions_pe or mentions_margin)
    notes = (
        "Passed audit: explicit rating and core metrics verified."
        if passed
        else "Flagged: Missing structured metrics citation."
    )

    return {
        "final_report": report,
        "passed_guardrail": passed,
        "audit_notes": notes,
    }

# 6. Build and Compile the Graph
workflow = StateGraph(ResearchState)

workflow.add_node("fundamental_analyst", fundamental_analyst)
workflow.add_node("sentiment_analyst", sentiment_analyst)
workflow.add_node("chief_arbiter", chief_arbiter)
workflow.add_node("evaluator_guardrail", evaluator_guardrail)

# Edge wiring: Run both analysts first, then synthesize
workflow.add_edge(START, "fundamental_analyst")
workflow.add_edge("fundamental_analyst", "sentiment_analyst")
workflow.add_edge("sentiment_analyst", "chief_arbiter")
workflow.add_edge("chief_arbiter", "evaluator_guardrail")
workflow.add_edge("evaluator_guardrail", END)

research_graph = workflow.compile()

if __name__ == "__main__":
    from ingest import fetch_ticker_data
    from store import store_news

    symbol = "NVDA"
    print(f"1. Fetching live data for {symbol}...")
    payload = fetch_ticker_data(symbol)

    print(f"2. Syncing news to ChromaDB...")
    store_news(symbol, payload.news)

    print(f"3. Executing LangGraph Multi-Agent Engine...")
    initial_state: ResearchState = {
        "ticker": symbol,
        "metrics": payload.metrics.model_dump(),
        "fundamental_analysis": None,
        "sentiment_analysis": None,
        "final_report": None,
        "passed_guardrail": None,
        "audit_notes": None
    }

    final_output = research_graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print(f" FINAL INVESTMENT REPORT: {symbol}")
    print("=" * 60)
    print(final_output.get("final_report"))

    print("\n" + "-" * 60)
    print(" AUDIT & GUARDRAIL RESULTS")
    print("-" * 60)
    print(f"Passed Audit : {final_output.get('passed_guardrail')}")
    print(f"Audit Notes  : {final_output.get('audit_notes')}")



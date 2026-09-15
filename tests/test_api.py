import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from database import create_db_and_tables
from ingest import FinancialMetrics, TickerPayload
from graph import evaluator_guardrail, ResearchState

#Have to create tables for sql test database
@pytest.fixture(autouse=True)
def setup_test_db():
    create_db_and_tables()

client = TestClient(app)

# health endpoint check

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online"}



# Schema Evaluation check

def test_pydantic_metrics_validation():
    valid_data = {
        "ticker": "NVDA",
        "current_price": 125.50,
        "trailing_pe": 45.2,
        "forward_pe": 32.1,
        "peg_ratio": 1.4,
        "debt_to_equity": 0.35,
        "profit_margins": 0.55,
        "free_cashflow": 25000000000.0,
    }

    metrics = FinancialMetrics(**valid_data)
    assert metrics.ticker == "NVDA"
    assert metrics.current_price == 125.50


    # Making sure GuardRail Logic Works
    def test_guardrail_pass():
        mock_state: ResearchState = {
            "ticker": "NVDA",
            "metrics": {"trailing_pe": 45.2, "profit_margins": 0.55},
            "fundamental_analysis": "Solid fundamentals.",
            "sentiment_analysis": "Positive catalysts.",
            "final_report": "RECOMMENDATION: BUY. The P/E ratio of 45 is justified given strong margins.",
            "passed_guardrail": None,
            "audit_notes": None,
        }
        result = evaluator_guardrail(mock_state)
        assert result["passed_guardrail"] is True
        assert "Passed audit" in result["audit_notes"]



    def test_guardrail_failure_missing_verdict():
        mock_state: ResearchState = {
            "ticker": "NVDA",
            "metrics": {"trailing_pe": 45.2},
            "fundamental_analysis": "Solid.",
            "sentiment_analysis": "Bullish.",
            "final_report": "This company has a good P/E ratio, but no recommendation is provided.",
            "passed_guardrail": None,
            "audit_notes": None,
        }
        result = evaluator_guardrail(mock_state)
        assert result["passed_guardrail"] is False
        assert "Flagged" in result["audit_notes"]




# Mock Route Integration Test

@patch("main.fetch_ticker_data")
@patch("main.store_news")
@patch("main.research_graph.invoke")
def test_research_endpoint_flow(mock_invoke, mock_store_news, mock_fetch):

    mock_metrics = FinancialMetrics(
        ticker="TEST",
        current_price=100.0,
        trailing_pe=20.0,
        forward_pe=18.0,
        peg_ratio=1.1,
        debt_to_equity=0.2,
        profit_margins=0.25,
        free_cashflow=1000000.0
    )

    mock_fetch.return_value = TickerPayload(ticker="TEST", metrics=mock_metrics, news=[])
    mock_invoke.return_value = {
        "final_report": "BUY rating based on P/E and profit margins.",
        "passed_guardrail": True,
        "audit_notes": "Passed audit."
    }


    response = client.post("/api/v1/research/TEST")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TEST"
    assert data["passed_guardrail"] is True
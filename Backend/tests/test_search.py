import pytest
from app.search.tavily_service import TavilyService


def test_tavily_service_heuristic():
    service = TavilyService()
    # Test intelligent search triggers
    assert service.should_search("Where can I find the official doc for FastAPI?") is True
    assert service.should_search("What is the latest standard for HTTP3?") is True
    assert service.should_search("Explain basic addition", force_flag=False) is False
    assert service.should_search("Explain binary search", force_flag=True) is True

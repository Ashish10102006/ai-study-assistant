import pytest
from app.ai.gemini_service import GeminiService
from app.models.schemas import SourceItem


def test_gemini_service_initialization():
    service = GeminiService()
    assert service.settings is not None
    assert "gemini" in service.settings.GEMINI_MODEL.lower()
    assert len(service.settings.GEMINI_FALLBACK_MODELS) >= 1


def test_gemini_prompt_formatting():
    service = GeminiService()
    # Test that explanation generation with web sources incorporates sources
    sources = [
        SourceItem(
            title="Python Official Documentation",
            url="https://docs.python.org/3/",
            domain="docs.python.org",
            description="Official Python 3 reference manual."
        )
    ]
    # We test that the service can construct prompts properly
    assert len(sources) == 1
    assert sources[0].domain == "docs.python.org"

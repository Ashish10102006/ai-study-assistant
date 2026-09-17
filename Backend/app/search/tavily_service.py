import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from app.config.settings import get_settings
from app.models.schemas import SourceItem

logger = logging.getLogger("ai_study_assistant.tavily")


class TavilyService:
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._init_client()

    def _init_client(self):
        if not self.settings.TAVILY_API_KEY:
            logger.warning("TAVILY_API_KEY not configured.")
            return

        try:
            from tavily import TavilyClient
            self._client = TavilyClient(api_key=self.settings.TAVILY_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            self._client = None

    def should_search(self, question: str, force_flag: Optional[bool] = None) -> bool:
        """
        Determines intelligently if web search improves the academic answer.
        Returns True if forced, or if question mentions documentation, latest updates,
        specific framework versions, official sources, or tutorials.
        """
        if force_flag is True:
            return True
        if force_flag is False:
            return False

        q = question.lower()
        search_indicators = [
            "documentation", "official doc", "latest", "recent", "resource",
            "tutorial", "link", "where to learn", "reference", "current version",
            "github", "papers", "standard", "rfc", "w3c", "release"
        ]
        return any(term in q for term in search_indicators)

    def search(self, query: str, max_results: int = 4) -> List[SourceItem]:
        """
        Performs web search via Tavily API and extracts REAL source items.
        Strictly returns only authentic results retrieved from the API.
        Never fabricates links or citations.
        """
        if not self._client:
            logger.warning("Tavily client unavailable. Cannot perform web search.")
            return []

        try:
            # Query Tavily API
            response = self._client.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_domains=None,
                exclude_domains=None
            )

            raw_results = response.get("results", [])
            sources: List[SourceItem] = []

            for r in raw_results:
                raw_url = r.get("url", "").strip()
                if not raw_url:
                    continue

                # Parse domain
                domain = urlparse(raw_url).netloc.replace("www.", "")
                title = r.get("title", "Educational Resource").strip()
                content = r.get("content", "").strip()

                sources.append(SourceItem(
                    title=title,
                    url=raw_url,
                    domain=domain,
                    description=content[:240] + ("..." if len(content) > 240 else ""),
                    is_live=True
                ))

            return sources

        except Exception as e:
            logger.error(f"Tavily search execution failed: {e}")
            return []


_tavily_instance: Optional[TavilyService] = None

def get_tavily_service() -> TavilyService:
    global _tavily_instance
    if _tavily_instance is None:
        _tavily_instance = TavilyService()
    return _tavily_instance

import re
import logging
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

logger = logging.getLogger("ai_study_assistant.rag.router")


class QueryIntent(str, Enum):
    DOCUMENT_RAG = "DOCUMENT_RAG"
    WEB_SEARCH = "WEB_SEARCH"
    GENERAL_ACADEMIC = "GENERAL_ACADEMIC"
    HYBRID_DOC_AND_WEB = "HYBRID_DOC_AND_WEB"


class RoutingDecision(BaseModel):
    intent: QueryIntent
    use_document: bool
    use_web: bool
    reasoning: str
    confidence: float
    extracted_keywords: List[str] = []


class AdaptiveRouter:
    """
    Intelligent query understanding and adaptive routing engine.
    Inspects student question semantics, active document context,
    and search flags to determine the optimal retrieval pathway.
    """

    # Indicators that the question refers to uploaded materials (allowing optional subject descriptor like 'DBMS notes')
    DOC_INDICATORS = [
        r"\b(my|the|uploaded|this)(\s+[a-zA-Z0-9_\-]+){0,3}\s+(notes?|pdf|slides?|doc(ument)?|textbook|syllabus|lecture|file|chapter)\b",
        r"\baccording to\s+(my|the|uploaded|this)(\s+[a-zA-Z0-9_\-]+){0,2}\s+(notes?|pdf|doc|lecture|slides?)\b",
        r"\bmentioned in\s+(my|the|uploaded|this)(\s+[a-zA-Z0-9_\-]+){0,2}\s+(notes?|pdf|slides?|document)\b",
        r"\bfrom\s+(my|the|uploaded|this)(\s+[a-zA-Z0-9_\-]+){0,3}\s+(notes?|pdf|slides?|document|syllabus)\b",
        r"\bin page \d+\b",
        r"\bslide \d+\b",
    ]

    # Indicators for real-time / web-search required queries
    WEB_INDICATORS = [
        r"\b(latest|current|recent|newest|today|now|2024|2025|2026)\b",
        r"\b(latest version|release date|documentation|changelog)\b",
        r"\b(pricing|stock price|live status|current events?|market share)\b",
        r"\b(compare with latest|current industry standards?)\b",
        r"\b(official docs?|official website|github repo)\b",
    ]

    # Indicators for hybrid queries requiring both document and live web
    HYBRID_INDICATORS = [
        r"\bcompare\b.*?\b(notes?|pdf|slides?|syllabus).*?\b(latest|current|web|industry|modern)\b",
        r"\b(does|is)\b.*?\b(notes?|pdf|slides?).*?\b(current|latest|modern|outdated|deprecated|valid)\b",
        r"\b(notes?|pdf|slides?).*?\b(with|against|and)\b.*?\b(current|latest|web|modern)\b",
    ]

    def route(
        self,
        query: str,
        document_id: Optional[str] = None,
        use_web_search: Optional[bool] = None,
        has_user_documents: bool = False
    ) -> RoutingDecision:
        """
        Evaluates the query and returns an authoritative RoutingDecision.
        """
        q = query.strip().lower()
        keywords = self._extract_keywords(q)

        # Explicit user web search override
        if use_web_search is True and not document_id:
            return RoutingDecision(
                intent=QueryIntent.WEB_SEARCH,
                use_document=False,
                use_web=True,
                reasoning="User explicitly requested web search grounding.",
                confidence=1.0,
                extracted_keywords=keywords
            )

        # Check hybrid indicator first
        for pattern in self.HYBRID_INDICATORS:
            if re.search(pattern, q):
                return RoutingDecision(
                    intent=QueryIntent.HYBRID_DOC_AND_WEB,
                    use_document=True,
                    use_web=True,
                    reasoning="Query requests comparison between course document context and current web info.",
                    confidence=0.95,
                    extracted_keywords=keywords
                )

        # Explicit document attachment provided
        if document_id:
            # Check if user specifically asks for web augmentation within the document question
            if use_web_search is True or any(re.search(pat, q) for pat in self.WEB_INDICATORS):
                return RoutingDecision(
                    intent=QueryIntent.HYBRID_DOC_AND_WEB,
                    use_document=True,
                    use_web=True,
                    reasoning="Document attached with live web verification requested.",
                    confidence=0.9,
                    extracted_keywords=keywords
                )

            return RoutingDecision(
                intent=QueryIntent.DOCUMENT_RAG,
                use_document=True,
                use_web=False,
                reasoning="Document explicitly attached; executing Adaptive Document RAG.",
                confidence=0.98,
                extracted_keywords=keywords
            )

        # Check document indicators in question text (even without explicit document_id)
        doc_match = any(re.search(pat, q) for pat in self.DOC_INDICATORS)
        if doc_match and has_user_documents:
            return RoutingDecision(
                intent=QueryIntent.DOCUMENT_RAG,
                use_document=True,
                use_web=False,
                reasoning="Query references uploaded notes/document; routing to user document collection.",
                confidence=0.88,
                extracted_keywords=keywords
            )

        # Check web search indicators
        web_match = any(re.search(pat, q) for pat in self.WEB_INDICATORS)
        if web_match and use_web_search is not False:
            return RoutingDecision(
                intent=QueryIntent.WEB_SEARCH,
                use_document=False,
                use_web=True,
                reasoning="Query involves temporal or external live facts; routing to Tavily search.",
                confidence=0.92,
                extracted_keywords=keywords
            )

        # Default fallback: General Educational Question
        return RoutingDecision(
            intent=QueryIntent.GENERAL_ACADEMIC,
            use_document=False,
            use_web=False,
            reasoning="Foundational academic concept; generating direct pedagogical explanation via Gemini.",
            confidence=0.95,
            extracted_keywords=keywords
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """Extracts high-value technical and academic tokens from query."""
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
            "is", "are", "was", "were", "what", "how", "why", "explain", "describe",
            "my", "notes", "pdf", "can", "you", "tell", "me", "about", "please"
        }
        tokens = re.findall(r"[a-zA-Z0-9_\-\+\#]{2,}", text)
        return [t for t in tokens if t.lower() not in stopwords][:10]


_adaptive_router: Optional[AdaptiveRouter] = None


def get_adaptive_router() -> AdaptiveRouter:
    global _adaptive_router
    if _adaptive_router is None:
        _adaptive_router = AdaptiveRouter()
    return _adaptive_router

import re
import logging
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel

logger = logging.getLogger("ai_study_assistant.rag.grounding")

# Stopwords to filter out so that only substantive domain terms are evaluated
ACADEMIC_STOPWORDS: Set[str] = {
    # Common English functional words
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't",
    "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's",
    "when", "when's", "where", "where's", "which", "while", "who", "who's", "whom",
    "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll",
    "you're", "you've", "your", "yours", "yourself", "yourselves",
    # Conversational & question framing boilerplate
    "notes", "pdf", "document", "file", "lecture", "slide", "slides", "uploaded",
    "explain", "tell", "describe", "discuss", "mention", "mentioned", "give", "define",
    "definition", "according", "summary", "summarize", "page", "chapter", "detail",
    "details", "please", "help", "information", "info", "state", "states", "show", "shows"
}


class GroundingStatus(str, Enum):
    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"


class GroundingDecision(BaseModel):
    status: GroundingStatus
    relevance_score: float
    best_chunk_id: Optional[str] = None
    substantive_coverage: float
    dense_similarity: float
    matched_terms: List[str] = []
    missing_terms: List[str] = []
    reasoning: str


class GroundingEvaluator:
    """
    Strict Document Grounding Evaluator.
    Evaluates whether retrieved document chunks actually contain evidence
    and substantive support for the student's question before generation.
    """

    @classmethod
    def extract_substantive_terms(cls, query: str) -> List[str]:
        """Extracts substantive domain terms, filtering out stopwords and question fluff."""
        raw_tokens = re.findall(r"[a-zA-Z0-9_\-\+]{2,}", query.lower())
        substantive = []
        for t in raw_tokens:
            if t not in ACADEMIC_STOPWORDS and len(t) >= 3:
                substantive.append(t)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for s in substantive:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        return deduped

    @classmethod
    def evaluate(
        cls,
        query: str,
        candidates: List[Dict[str, Any]],
        document_meta: Optional[Dict[str, Any]] = None
    ) -> GroundingDecision:
        """
        Calculates grounding evidence across candidate chunks.
        Determines if question is STRONGLY_SUPPORTED, PARTIALLY_SUPPORTED, or NOT_SUPPORTED.
        """
        if not candidates:
            return GroundingDecision(
                status=GroundingStatus.NOT_SUPPORTED,
                relevance_score=0.0,
                best_chunk_id=None,
                substantive_coverage=0.0,
                dense_similarity=0.0,
                matched_terms=[],
                missing_terms=cls.extract_substantive_terms(query),
                reasoning="No candidate chunks retrieved for this document."
            )

        substantive_terms = cls.extract_substantive_terms(query)
        total_substantive = len(substantive_terms)
        clean_query = query.strip().lower()

        # Concatenate candidate contents for collection-level term presence
        combined_text = " ".join([c.get("content", "").lower() for c in candidates])

        matched_terms = [t for t in substantive_terms if t in combined_text]
        missing_terms = [t for t in substantive_terms if t not in combined_text]

        coverage = (len(matched_terms) / total_substantive) if total_substantive > 0 else 0.5

        # Check individual chunks for maximum chunk-level quality
        best_relevance = 0.0
        best_chunk_id = None
        best_dense_sim = 0.0

        for chunk in candidates:
            content = chunk.get("content", "").lower()
            cid = chunk.get("id")

            # Dense similarity
            dense_sim = float(chunk.get("dense_score", 0.0) or 0.0)
            best_dense_sim = max(best_dense_sim, dense_sim)

            # Chunk-level term coverage
            chunk_matched = sum(1 for t in substantive_terms if t in content)
            chunk_coverage = (chunk_matched / total_substantive) if total_substantive > 0 else 0.5

            # Exact phrase match
            exact_phrase = 1.0 if clean_query in content else 0.0

            # Normalized dense similarity (typical text-embedding-004 baseline: 0.30 unrelated -> 0.75+ related)
            dense_norm = max(0.0, min(1.0, (dense_sim - 0.30) / 0.45))

            # Composite chunk relevance
            chunk_relevance = (
                0.40 * dense_norm +
                0.40 * chunk_coverage +
                0.15 * exact_phrase +
                0.05 * min(1.0, float(chunk.get("keyword_score", 0.0) or 0.0) / 4.0)
            )

            if chunk_relevance > best_relevance:
                best_relevance = chunk_relevance
                best_chunk_id = cid

        # Observability logging
        logger.info(
            f"Grounding Evaluation | Query: '{query[:50]}' | "
            f"Substantive Terms: {substantive_terms} | Matched: {matched_terms} | "
            f"Coverage: {coverage:.2f} | Best Dense Sim: {best_dense_sim:.4f} | "
            f"Best Chunk Relevance: {best_relevance:.4f}"
        )

        # -------------------------------------------------------------
        # GROUNDING DECISION LOGIC
        # -------------------------------------------------------------
        # Condition 1: If substantive terms exist, but NONE of them appear in any retrieved chunk
        if total_substantive > 0 and len(matched_terms) == 0 and best_dense_sim < 0.58:
            return GroundingDecision(
                status=GroundingStatus.NOT_SUPPORTED,
                relevance_score=round(best_relevance, 4),
                best_chunk_id=best_chunk_id,
                substantive_coverage=0.0,
                dense_similarity=round(best_dense_sim, 4),
                matched_terms=[],
                missing_terms=missing_terms,
                reasoning=(
                    f"None of the substantive query keywords ({missing_terms[:5]}) were found in "
                    f"the document chunks, and semantic similarity ({best_dense_sim:.3f}) is insufficient."
                )
            )

        # Condition 2: Overall relevance is too low to claim support
        if best_relevance < 0.28 and coverage < 0.35 and best_dense_sim < 0.50:
            return GroundingDecision(
                status=GroundingStatus.NOT_SUPPORTED,
                relevance_score=round(best_relevance, 4),
                best_chunk_id=best_chunk_id,
                substantive_coverage=round(coverage, 4),
                dense_similarity=round(best_dense_sim, 4),
                matched_terms=matched_terms,
                missing_terms=missing_terms,
                reasoning=(
                    f"Overall relevance score ({best_relevance:.3f}) and term coverage ({coverage:.2f}) "
                    f"fall below the grounding evidence threshold."
                )
            )

        # Condition 3: Strongly Supported
        # High coverage AND reasonable semantic similarity, OR exact phrase match
        if (coverage >= 0.65 and best_dense_sim >= 0.45) or (best_relevance >= 0.55) or (clean_query in combined_text):
            return GroundingDecision(
                status=GroundingStatus.STRONGLY_SUPPORTED,
                relevance_score=round(best_relevance, 4),
                best_chunk_id=best_chunk_id,
                substantive_coverage=round(coverage, 4),
                dense_similarity=round(best_dense_sim, 4),
                matched_terms=matched_terms,
                missing_terms=missing_terms,
                reasoning=(
                    f"Strong evidence found in document chunks: coverage={coverage:.2f}, "
                    f"relevance={best_relevance:.3f}, dense_sim={best_dense_sim:.3f}."
                )
            )

        # Condition 4: Partially Supported
        # Some terms are present, but key discriminating terms are missing
        return GroundingDecision(
            status=GroundingStatus.PARTIALLY_SUPPORTED,
            relevance_score=round(best_relevance, 4),
            best_chunk_id=best_chunk_id,
            substantive_coverage=round(coverage, 4),
            dense_similarity=round(best_dense_sim, 4),
            matched_terms=matched_terms,
            missing_terms=missing_terms,
            reasoning=(
                f"Partial evidence found: matched terms={matched_terms}, missing terms={missing_terms}. "
                f"Coverage={coverage:.2f}, relevance={best_relevance:.3f}."
            )
        )


_evaluator_instance: Optional[GroundingEvaluator] = None


def get_grounding_evaluator() -> GroundingEvaluator:
    global _evaluator_instance
    if _evaluator_instance is None:
        _evaluator_instance = GroundingEvaluator()
    return _evaluator_instance

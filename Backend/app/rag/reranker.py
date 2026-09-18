import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("ai_study_assistant.rag.reranker")


class ContextualReranker:
    """
    Reranks candidates produced by RRF fusion using query-term density,
    heading alignment, and contextual coherence, before selecting top-K context.
    """

    def __init__(self, top_k: int = 4):
        self.top_k = top_k

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        document_meta: Dict[str, Any] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Reranks RRF candidates and returns:
        (top_chunks, structured_citations)
        """
        if not candidates:
            return [], []

        from app.rag.grounding import GroundingEvaluator
        substantive_terms = GroundingEvaluator.extract_substantive_terms(query)
        clean_query = query.strip().lower()
        scored_candidates: List[Tuple[Dict[str, Any], float]] = []

        for candidate in candidates:
            content = candidate.get("content", "").lower()
            metadata = candidate.get("metadata") or {}
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except Exception:
                    metadata = {}

            section = str(metadata.get("section", "")).lower()

            # 1. Substantive Term Coverage Score (Ignores filler and stop words)
            if substantive_terms:
                matched_substantive = sum(1 for term in substantive_terms if term in content)
                coverage = (matched_substantive / len(substantive_terms))
            else:
                coverage = 0.5

            # 2. Section Heading Alignment
            section_bonus = 0.0
            if section and substantive_terms:
                for term in substantive_terms:
                    if term in section:
                        section_bonus += 0.35

            # 3. Exact Substring Match Bonus
            exact_bonus = 0.5 if clean_query in content else 0.0

            # 4. Dense Semantic Similarity Score
            dense_score = float(candidate.get("dense_score", 0.0) or 0.0)
            dense_bonus = max(0.0, min(1.0, (dense_score - 0.30) / 0.45)) * 0.40

            # 5. Prior RRF Score
            rrf_score = float(candidate.get("rrf_score", 0.0) or 0.0)

            # Combined Rerank Score
            final_score = (coverage * 0.45) + section_bonus + exact_bonus + dense_bonus + (rrf_score * 5.0)

            # Attach computed scores onto candidate dictionary for downstream observability
            candidate["rerank_score"] = round(final_score, 4)
            candidate["substantive_coverage"] = round(coverage, 4)

            scored_candidates.append((candidate, final_score))

        # Sort descending by final rerank score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:self.top_k]

        selected_chunks: List[Dict[str, Any]] = []
        citations: List[Dict[str, Any]] = []

        filename = (document_meta or {}).get("file_name", "Document")

        for chunk, score in top_candidates:
            selected_chunks.append(chunk)

            meta = chunk.get("metadata") or {}
            if isinstance(meta, str):
                import json
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            page_num = meta.get("page", 1)
            section_title = meta.get("section", "")

            # Formulate structured citation item
            citations.append({
                "document_id": chunk.get("document_id"),
                "file_name": filename,
                "chunk_index": chunk.get("chunk_index", 0),
                "page": page_num,
                "section": section_title or "General Section",
                "snippet": chunk.get("content", "")[:180] + ("..." if len(chunk.get("content", "")) > 180 else ""),
                "score": round(score, 4)
            })

        return selected_chunks, citations

    @staticmethod
    def evaluate_grounding(query: str, chunks: List[Dict[str, Any]], document_meta: Dict[str, Any] = None, is_summary: bool = False):
        """Delegates grounding decision to GroundingEvaluator."""
        from app.rag.grounding import GroundingEvaluator
        return GroundingEvaluator.evaluate(query, chunks, document_meta, is_summary=is_summary)

    @staticmethod
    def build_context_block(chunks: List[Dict[str, Any]], filename: str = "Uploaded Document") -> str:
        """
        Builds clear markdown context blocks with pinpoint citations for Gemini prompting.
        """
        if not chunks:
            return ""

        blocks = []
        for c in chunks:
            meta = c.get("metadata") or {}
            if isinstance(meta, str):
                import json
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}

            page = meta.get("page", 1)
            section = meta.get("section", "")
            header = f"[Document: {filename} | Page {page}" + (f" | Section: {section}" if section else "") + "]"
            blocks.append(f"{header}\n{c.get('content', '')}")

        return "\n\n---\n\n".join(blocks)


_contextual_reranker: ContextualReranker = ContextualReranker(top_k=4)


def get_contextual_reranker() -> ContextualReranker:
    return _contextual_reranker

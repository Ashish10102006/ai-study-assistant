import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.rag.embeddings import get_embedding_service, EmbeddingService
from app.services.storage_service import get_storage_service

logger = logging.getLogger("ai_study_assistant.rag.retriever")


class HybridRetriever:
    """
    Dual-track hybrid retriever executing Dense Semantic Search (embeddings)
    and Sparse Keyword Full-Text Search, fused via Reciprocal Rank Fusion (RRF).
    Guarantees strict tenant isolation by checking user_id on all document queries.
    """

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k
        self.embedding_service = get_embedding_service()
        self.storage = get_storage_service()

    def retrieve(
        self,
        query: str,
        document_id: str,
        user_id: str,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval on the specified document:
        1. Embeds query into 768-dim vector.
        2. Performs dense vector similarity search.
        3. Performs sparse keyword / full-text search.
        4. Fuses ranked lists using Reciprocal Rank Fusion (RRF).
        5. Returns top fused candidates with chunk content and metadata.
        """
        # Verify document exists and belongs to this user (Tenant Isolation Guard)
        doc = self.storage.get_document(document_id, user_id)
        if not doc:
            logger.warning(f"Tenant isolation: Document {document_id} not found for user {user_id}")
            return []

        # Retrieve all raw chunks for this document from storage
        raw_chunks = self.storage.get_raw_chunks_with_embeddings(document_id)
        if not raw_chunks:
            return []

        # 1. Vector Search
        query_vector = self.embedding_service.embed_text(query)
        dense_ranked = self._vector_search(query_vector, raw_chunks)

        # 2. Keyword Search
        keyword_ranked = self._keyword_search(query, raw_chunks)

        # 3. Reciprocal Rank Fusion (RRF)
        fused_candidates = self._reciprocal_rank_fusion(dense_ranked, keyword_ranked, top_k=top_k)

        return fused_candidates

    def _vector_search(
        self,
        query_vector: List[float],
        chunks: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Computes cosine similarity between query vector and chunk embeddings."""
        scored: List[Tuple[Dict[str, Any], float]] = []

        for chunk in chunks:
            emb = chunk.get("embedding")
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    emb = None

            if emb and isinstance(emb, list):
                sim = EmbeddingService.cosine_similarity(query_vector, emb)
            else:
                # If chunk has no embedding, fallback to lightweight query embedding against chunk content
                fallback_emb = self.embedding_service._generate_fallback_embedding(chunk.get("content", ""))
                sim = EmbeddingService.cosine_similarity(query_vector, fallback_emb)

            scored.append((chunk, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _keyword_search(
        self,
        query: str,
        chunks: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Performs token-frequency keyword matching with case-insensitive matching."""
        query_tokens = [t.lower() for t in query.split() if len(t) > 2]
        if not query_tokens:
            query_tokens = [query.lower()]

        scored: List[Tuple[Dict[str, Any], float]] = []

        for chunk in chunks:
            content = chunk.get("content", "").lower()
            score = 0.0

            for token in query_tokens:
                # Count occurrences
                count = content.count(token)
                if count > 0:
                    # Log-scaled token frequency
                    score += 1.0 + (count - 1) * 0.2

            # Exact phrase bonus
            if query.lower() in content:
                score += 3.0

            scored.append((chunk, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Tuple[Dict[str, Any], float]],
        keyword_results: List[Tuple[Dict[str, Any], float]],
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Combines two ranked lists using RRF score:
        RRF_Score(d) = 1 / (k + rank_dense) + 1 / (k + rank_keyword)
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}
        dense_ranks: Dict[str, int] = {}
        keyword_ranks: Dict[str, int] = {}
        dense_scores: Dict[str, float] = {}
        keyword_scores: Dict[str, float] = {}

        for rank, (chunk, score) in enumerate(dense_results):
            cid = chunk["id"]
            chunk_map[cid] = chunk
            dense_ranks[cid] = rank + 1
            dense_scores[cid] = float(score)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        for rank, (chunk, score) in enumerate(keyword_results):
            cid = chunk["id"]
            chunk_map[cid] = chunk
            keyword_ranks[cid] = rank + 1
            keyword_scores[cid] = float(score)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        fused: List[Dict[str, Any]] = []
        for cid in sorted_cids[:top_k]:
            c = dict(chunk_map[cid])
            c["rrf_score"] = round(rrf_scores[cid], 5)
            c["dense_rank"] = dense_ranks.get(cid)
            c["keyword_rank"] = keyword_ranks.get(cid)
            c["dense_score"] = round(dense_scores.get(cid, 0.0), 4)
            c["keyword_score"] = round(keyword_scores.get(cid, 0.0), 4)
            fused.append(c)

        return fused

    def retrieve_for_summary(
        self,
        document_id: str,
        user_id: str,
        max_chunks: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Retrieves representative chunks across the entire document sequentially for summarization.
        Enforces strict tenant isolation.
        Preserves natural reading order (chunk_index ASC) for coherent document overview synthesis.
        """
        # 1. Tenant Isolation: Verify document exists and belongs to this user
        doc = self.storage.get_document(document_id, user_id)
        if not doc:
            logger.warning(f"Tenant isolation: Document {document_id} not found for user {user_id}")
            return []

        # 2. Retrieve all raw chunks for this document from storage
        raw_chunks = self.storage.get_raw_chunks_with_embeddings(document_id)
        if not raw_chunks:
            return []

        # 3. Filter to chunks with actual readable content
        valid_chunks = [c for c in raw_chunks if c.get("content", "").strip()]
        if not valid_chunks:
            return []

        total = len(valid_chunks)
        if total <= max_chunks:
            selected = valid_chunks
        else:
            # Controlled representative multi-stage sampling:
            # - beginning (introduction, title, objectives, table of contents)
            # - evenly-spaced middle chunks (topics, sections)
            # - ending (conclusions, summary)
            head_count = min(3, max(1, total // 5))
            tail_count = min(3, max(1, total // 5))
            middle_count = max_chunks - (head_count + tail_count)

            selected_indices = set(range(head_count))
            selected_indices.update(range(total - tail_count, total))

            middle_pool = list(range(head_count, total - tail_count))
            if middle_pool and middle_count > 0:
                step = len(middle_pool) / float(middle_count)
                for i in range(middle_count):
                    idx = middle_pool[int(i * step)]
                    selected_indices.add(idx)

            sorted_indices = sorted(list(selected_indices))
            selected = [valid_chunks[i] for i in sorted_indices[:max_chunks]]

        results = []
        for c in selected:
            item = dict(c)
            item["dense_score"] = 1.0
            item["keyword_score"] = 1.0
            item["rrf_score"] = 1.0
            results.append(item)

        return results


_hybrid_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever() -> HybridRetriever:
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever()
    return _hybrid_retriever

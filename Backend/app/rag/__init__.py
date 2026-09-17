"""
Adaptive RAG Core Module
Combines Query Understanding/Adaptive Routing, Structure-Aware Contextual Embeddings,
Hybrid Retrieval (Dense Semantic Vector + Keyword FTS), Reciprocal Rank Fusion (RRF),
and Contextual Reranking.
"""

from app.rag.router import AdaptiveRouter, QueryIntent, RoutingDecision, get_adaptive_router
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.retriever import HybridRetriever, get_hybrid_retriever
from app.rag.reranker import ContextualReranker, get_contextual_reranker

__all__ = [
    "AdaptiveRouter",
    "QueryIntent",
    "RoutingDecision",
    "get_adaptive_router",
    "EmbeddingService",
    "get_embedding_service",
    "HybridRetriever",
    "get_hybrid_retriever",
    "ContextualReranker",
    "get_contextual_reranker",
]

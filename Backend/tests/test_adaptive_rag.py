import pytest
from fastapi.testclient import TestClient
from main import app

from app.rag.router import AdaptiveRouter, QueryIntent, get_adaptive_router
from app.rag.embeddings import EmbeddingService, get_embedding_service, EMBEDDING_DIMENSION
from app.rag.retriever import HybridRetriever, get_hybrid_retriever
from app.rag.reranker import ContextualReranker, get_contextual_reranker
from app.documents.processor import get_document_processor
from app.services.storage_service import get_storage_service

client = TestClient(app)


# ==============================================================================
# 1. ADAPTIVE ROUTER TESTS
# ==============================================================================
def test_adaptive_router_document_rag():
    router = get_adaptive_router()

    # Query referring to uploaded notes
    decision1 = router.route("Explain normalization from my DBMS notes", has_user_documents=True)
    assert decision1.intent == QueryIntent.DOCUMENT_RAG
    assert decision1.use_document is True
    assert decision1.use_web is False

    # Attached document ID provided
    decision2 = router.route("What is the time complexity of AVL tree insertions?", document_id="doc-12345")
    assert decision2.intent == QueryIntent.DOCUMENT_RAG
    assert decision2.use_document is True
    assert decision2.use_web is False


def test_adaptive_router_web_search():
    router = get_adaptive_router()

    # Query with temporal/live indicator
    decision1 = router.route("What is the latest version of Python and its new release date?")
    assert decision1.intent == QueryIntent.WEB_SEARCH
    assert decision1.use_web is True
    assert decision1.use_document is False

    # Force web search flag
    decision2 = router.route("Explain React server components", use_web_search=True)
    assert decision2.intent == QueryIntent.WEB_SEARCH
    assert decision2.use_web is True


def test_adaptive_router_general_academic():
    router = get_adaptive_router()

    # Foundational concept without document or temporal cue
    decision = router.route("Explain recursion in simple words with base case example")
    assert decision.intent == QueryIntent.GENERAL_ACADEMIC
    assert decision.use_document is False
    assert decision.use_web is False


def test_adaptive_router_hybrid_doc_and_web():
    router = get_adaptive_router()

    # Query comparing notes against current web standard
    decision = router.route(
        "Compare my notes on React state management with current modern industry standards",
        document_id="doc-999"
    )
    assert decision.intent == QueryIntent.HYBRID_DOC_AND_WEB
    assert decision.use_document is True
    assert decision.use_web is True


# ==============================================================================
# 2. EMBEDDINGS & SIMILARITY TESTS
# ==============================================================================
def test_embedding_service_dimensions_and_math():
    embedder = get_embedding_service()

    vec = embedder.embed_text("Database normalization 1NF 2NF 3NF BCNF")
    assert len(vec) == EMBEDDING_DIMENSION

    # Identical vector cosine similarity must be 1.0 (or ~0.9999 due to floating point)
    sim_self = embedder.cosine_similarity(vec, vec)
    assert pytest.approx(sim_self, abs=1e-4) == 1.0

    # Orthogonal or zero vector similarity check
    zero_vec = [0.0] * EMBEDDING_DIMENSION
    assert embedder.cosine_similarity(vec, zero_vec) == 0.0

    # Semantic similarity: related sentences should score higher than unrelated ones
    vec_related = embedder.embed_text("Relational database table decomposition and candidate keys")
    vec_unrelated = embedder.embed_text("Cooking recipes for Italian tomato pasta and basil")

    sim_related = embedder.cosine_similarity(vec, vec_related)
    sim_unrelated = embedder.cosine_similarity(vec, vec_unrelated)
    assert sim_related > sim_unrelated


# ==============================================================================
# 3. STRUCTURE-AWARE CHUNKING TESTS
# ==============================================================================
def test_structure_aware_chunking_and_metadata():
    processor = get_document_processor()

    sections = [
        {
            "page": 1,
            "section": "Chapter 1: Operating System Concepts",
            "text": "Processes represent running programs with dedicated address spaces."
        },
        {
            "page": 2,
            "section": "Chapter 2: Threads and Concurrency",
            "text": "Threads share process memory but retain individual stack pointers."
        }
    ]

    chunks = processor.chunk_document(sections, doc_title="Operating_Systems.pdf")
    assert len(chunks) == 2

    c1 = chunks[0]
    assert c1["metadata"]["page"] == 1
    assert "Chapter 1" in c1["metadata"]["section"]
    assert c1["metadata"]["doc_title"] == "Operating_Systems.pdf"

    c2 = chunks[1]
    assert c2["metadata"]["page"] == 2
    assert "Chapter 2" in c2["metadata"]["section"]


# ==============================================================================
# 4. RECIPROCAL RANK FUSION (RRF) & RERANKER TESTS
# ==============================================================================
def test_reciprocal_rank_fusion_logic():
    retriever = HybridRetriever(rrf_k=60)

    dense_ranked = [
        ({"id": "chunk_1", "content": "Binary Search Trees maintain ordered node invariants."}, 0.92),
        ({"id": "chunk_2", "content": "B-Trees are self-balancing search trees for disk storage."}, 0.85),
    ]

    keyword_ranked = [
        ({"id": "chunk_2", "content": "B-Trees are self-balancing search trees for disk storage."}, 5.0),
        ({"id": "chunk_1", "content": "Binary Search Trees maintain ordered node invariants."}, 2.0),
    ]

    fused = retriever._reciprocal_rank_fusion(dense_ranked, keyword_ranked, top_k=2)
    assert len(fused) == 2
    # Both items should be present with calculated rrf_score
    ids = [f["id"] for f in fused]
    assert "chunk_1" in ids and "chunk_2" in ids
    assert fused[0]["rrf_score"] > 0.0


def test_contextual_reranker_selection_and_citations():
    reranker = get_contextual_reranker()

    candidates = [
        {
            "id": "c1",
            "document_id": "doc_os_1",
            "chunk_index": 0,
            "content": "A Process Control Block (PCB) contains register state, PID, and scheduling priority.",
            "metadata": {"page": 3, "section": "Process Management"},
            "rrf_score": 0.032
        },
        {
            "id": "c2",
            "document_id": "doc_os_1",
            "chunk_index": 1,
            "content": "Page replacement algorithms include LRU, FIFO, and Optimal.",
            "metadata": {"page": 12, "section": "Virtual Memory"},
            "rrf_score": 0.025
        }
    ]

    doc_meta = {"file_name": "OS_Lecture_Notes.pdf"}
    selected_chunks, citations = reranker.rerank(
        query="What information is stored inside the Process Control Block PCB?",
        candidates=candidates,
        document_meta=doc_meta
    )

    assert len(selected_chunks) >= 1
    # Top chunk should be c1 because of high keyword density ("PCB", "Process Control Block")
    assert selected_chunks[0]["id"] == "c1"
    assert len(citations) >= 1
    assert citations[0]["page"] == 3
    assert citations[0]["section"] == "Process Management"
    assert citations[0]["file_name"] == "OS_Lecture_Notes.pdf"


# ==============================================================================
# 5. TENANT ISOLATION & SECURITY TEST
# ==============================================================================
def test_tenant_isolation_in_retrieval():
    storage = get_storage_service()
    retriever = get_hybrid_retriever()

    user_a = "student_alice_uuid_101"
    user_b = "student_bob_uuid_202"

    # Alice uploads a document
    doc_a = storage.save_document(
        user_id=user_a,
        file_name="Alice_Private_Notes.txt",
        file_type="text/plain",
        file_size=1024,
        storage_path="mock_path_a"
    )
    storage.save_document_chunks(doc_a["id"], [
        {
            "content": "Alice's secret exam preparation formulas for Cryptography.",
            "metadata": {"page": 1, "section": "RSA Key Generation"}
        }
    ])

    # Bob attempts to retrieve Alice's document
    bob_retrieval = retriever.retrieve(
        query="secret exam preparation formulas",
        document_id=doc_a["id"],
        user_id=user_b,  # Attacking or probing user
        top_k=5
    )

    # Must return empty list due to strict tenant verification
    assert bob_retrieval == []

    # Clean up
    storage.delete_document(doc_a["id"], user_a)


# ==============================================================================
# 6. END-TO-END ADAPTIVE API FLOWS
# ==============================================================================
def test_api_adaptive_rag_endpoints():
    # 1. Ask general academic query
    res = client.post("/api/ask", json={
        "question": "What is the principle of mathematical induction in discrete mathematics?",
        "subject": "Mathematics",
        "explanation_mode": "simple"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["rag_mode"] == "adaptive"
    assert "routing_decision" in data
    assert data["routing_decision"]["intent"] in ["GENERAL_ACADEMIC", "WEB_SEARCH"]
    assert "answer" in data

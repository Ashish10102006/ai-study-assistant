import pytest
import uuid
from fastapi.testclient import TestClient
from main import app
from app.rag.grounding import GroundingEvaluator, GroundingStatus, GroundingDecision
from app.services.storage_service import get_storage_service
from app.rag.retriever import get_hybrid_retriever
from app.rag.reranker import get_contextual_reranker

client = TestClient(app)


def test_grounding_evaluator_supported_question():
    """TEST 1: Evaluator identifies strongly supported questions with substantive term matches."""
    chunks = [
        {
            "id": "chunk_1",
            "content": "A binary search tree (BST) is a rooted binary tree data structure with key ordering.",
            "dense_score": 0.78,
            "keyword_score": 4.0
        },
        {
            "id": "chunk_2",
            "content": "For every node X, keys in the left subtree are smaller than X.key, and keys in the right subtree are larger.",
            "dense_score": 0.72,
            "keyword_score": 3.0
        }
    ]

    decision = GroundingEvaluator.evaluate(
        query="Explain binary search tree key ordering in left and right subtree",
        candidates=chunks
    )

    assert decision.status == GroundingStatus.STRONGLY_SUPPORTED
    assert decision.substantive_coverage >= 0.70
    assert "ordering" in decision.matched_terms or "subtree" in decision.matched_terms
    assert decision.relevance_score >= 0.50


def test_grounding_evaluator_unsupported_question():
    """TEST 2: Evaluator identifies completely unsupported questions and denies grounding."""
    chunks = [
        {
            "id": "chunk_1",
            "content": "A binary search tree (BST) is a rooted binary tree data structure with key ordering.",
            "dense_score": 0.22,
            "keyword_score": 0.0
        },
        {
            "id": "chunk_2",
            "content": "Tree height is logarithmic O(log n) in balanced trees.",
            "dense_score": 0.19,
            "keyword_score": 0.0
        }
    ]

    decision = GroundingEvaluator.evaluate(
        query="What is the capital of France and what currency is used in Paris?",
        candidates=chunks
    )

    assert decision.status == GroundingStatus.NOT_SUPPORTED
    assert decision.substantive_coverage == 0.0
    assert len(decision.matched_terms) == 0
    assert "france" in decision.missing_terms or "capital" in decision.missing_terms
    assert decision.relevance_score < 0.28


def test_grounding_evaluator_semantically_similar_but_unsupported():
    """TEST 3: Topical similarity alone (data structures) must NOT prove support when discriminating concepts are absent."""
    chunks = [
        {
            "id": "chunk_1",
            "content": "Binary search trees maintain sorted keys. Inorder traversal produces ascending order.",
            "dense_score": 0.44,  # Moderate similarity because both are computer science data structures
            "keyword_score": 0.0
        },
        {
            "id": "chunk_2",
            "content": "The height of an unbalanced binary tree can degrade to O(n) worst case.",
            "dense_score": 0.41,
            "keyword_score": 0.0
        }
    ]

    # Query is about Fibonacci Heaps - related topic (data structures) but NOT in this BST document
    decision = GroundingEvaluator.evaluate(
        query="What is the amortized cost of decrease-key in a Fibonacci heap according to this document?",
        candidates=chunks
    )

    assert decision.status == GroundingStatus.NOT_SUPPORTED
    assert decision.substantive_coverage <= 0.20
    assert "fibonacci" in decision.missing_terms
    assert "heap" in decision.missing_terms


def test_grounding_evaluator_partial_information():
    """TEST 4: Evaluator detects partial support and identifies missing concept terms."""
    chunks = [
        {
            "id": "chunk_1",
            "content": "Binary search tree insertion takes O(h) time where h is the tree height.",
            "dense_score": 0.58,
            "keyword_score": 2.5
        }
    ]

    # Query asks for BST insertion (supported) AND Red-Black tree coloring (unsupported)
    decision = GroundingEvaluator.evaluate(
        query="Explain binary search tree insertion and Red-Black tree recoloring rules",
        candidates=chunks
    )

    assert decision.status == GroundingStatus.PARTIALLY_SUPPORTED
    assert "insertion" in decision.matched_terms
    assert "recoloring" in decision.missing_terms or "red-black" in decision.missing_terms


def test_api_document_grounding_end_to_end():
    """
    End-to-End API Test:
    1. Create a document for User A.
    2. Ask supported question -> Expect grounded answer.
    3. Ask unsupported question -> Expect refusal, NO general knowledge answer.
    4. Test User Isolation: User B cannot access User A's document.
    """
    storage = get_storage_service()
    user_a = f"guest_test_a_{uuid.uuid4().hex[:8]}"
    user_b = f"guest_test_b_{uuid.uuid4().hex[:8]}"

    # Save test document for User A
    doc_a = storage.save_document(
        user_id=user_a,
        file_name="operating_systems_paging.pdf",
        file_type="application/pdf",
        file_size=10240,
        storage_path="mock_path_os"
    )
    doc_id = doc_a["id"]

    # Ingest chunks
    storage.save_document_chunks(doc_id, [
        {
            "content": "Virtual memory paging divides physical memory into fixed-size blocks called page frames and logical memory into pages.",
            "metadata": {"page": 1, "section": "Memory Management"}
        },
        {
            "content": "The Translation Lookaside Buffer (TLB) is a high-speed hardware cache for page table entries to reduce memory access latency.",
            "metadata": {"page": 2, "section": "Hardware Acceleration"}
        }
    ])
    storage.update_document_status(doc_id, "COMPLETED")

    headers_a = {"X-Guest-ID": user_a}
    headers_b = {"X-Guest-ID": user_b}

    # --- 1. SUPPORTED QUESTION (via /api/documents/{id}/ask) ---
    resp_supported = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the Translation Lookaside Buffer TLB according to this document?"},
        headers=headers_a
    )
    assert resp_supported.status_code == 200
    data_supp = resp_supported.json()
    assert data_supp["document_used"] is True
    assert data_supp["routing_decision"]["grounding_decision"]["status"] in ("STRONGLY_SUPPORTED", "PARTIALLY_SUPPORTED")

    # --- 2. UNSUPPORTED QUESTION (via /api/documents/{id}/ask) ---
    resp_unsupported = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is the capital of France and what are the rules of cricket?"},
        headers=headers_a
    )
    assert resp_unsupported.status_code == 200
    data_unsupp = resp_unsupported.json()
    assert data_unsupp["document_used"] is True
    assert data_unsupp["citations"] == []
    assert data_unsupp["routing_decision"]["grounding_decision"]["status"] == "NOT_SUPPORTED"
    # CRITICAL VERIFICATION: Must explicitly state not supported, NO general knowledge answer
    assert "not supported" in data_unsupp["answer"].lower() or "couldn't find" in data_unsupp["answer"].lower()
    assert "paris" not in data_unsupp["answer"].lower()

    # --- 3. UNSUPPORTED QUESTION (via /api/ask with document_id) ---
    resp_ask_unsupp = client.post(
        "/api/ask",
        json={
            "question": "How does photosynthesis convert sunlight into glucose?",
            "document_id": doc_id
        },
        headers=headers_a
    )
    assert resp_ask_unsupp.status_code == 200
    data_ask_unsupp = resp_ask_unsupp.json()
    assert data_ask_unsupp["document_used"] is True
    assert data_ask_unsupp["routing_decision"]["grounding_decision"]["status"] == "NOT_SUPPORTED"
    assert "couldn't find this information in the uploaded document" in data_ask_unsupp["answer"].lower()
    assert "chlorophyll" not in data_ask_unsupp["answer"].lower()

    # --- 4. TENANT ISOLATION: User B tries to query User A's document ---
    resp_isolation = client.post(
        f"/api/documents/{doc_id}/ask",
        json={"question": "What is paging?"},
        headers=headers_b
    )
    assert resp_isolation.status_code == 404

    # Cleanup
    storage.delete_document(doc_id, user_a)

import os
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from main import app
from app.config.settings import get_settings
from app.ai.gemini_service import get_gemini_service
from app.search.tavily_service import get_tavily_service
from app.documents.processor import get_document_processor
from app.services.storage_service import get_storage_service
from app.services.supabase_client import get_supabase_admin, verify_user_token

client = TestClient(app)


# ==============================================================================
# 1. APPLICATION BOOT & HEALTH CHECK
# ==============================================================================
def test_app_starts_and_health_check():
    """Verify backend starts without errors and reports healthy diagnostics."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "AI STUDY ASSISTANT"
    assert data["services"]["uploads_ready"] is True


# ==============================================================================
# 2. SUPABASE CONNECTION & AUTHENTICATION
# ==============================================================================
def test_supabase_connection_and_auth():
    """Verify Supabase admin client initialization and token verification handling."""
    settings = get_settings()
    assert settings.SUPABASE_URL != ""
    assert settings.SUPABASE_SECRET_KEY != ""
    
    admin_client = get_supabase_admin()
    assert admin_client is not None

    # Invalid token handling returns None safely without unhandled crashes
    verified_user = verify_user_token("invalid_token_sample_12345")
    assert verified_user is None


# ==============================================================================
# 3. GEMINI API & CUSTOM ACADEMIC TOPIC INPUT
# ==============================================================================
def test_gemini_api_and_custom_academic_topic():
    """Verify Gemini API generates high-quality explanation for custom academic topic."""
    gemini = get_gemini_service()
    assert gemini is not None
    assert gemini.settings.GEMINI_API_KEY != ""

    custom_topic = "Dynamic Programming Bellman-Ford Algorithm"
    subject = "Computer Science"
    question = "Explain Bellman-Ford algorithm with time complexity and negative cycle detection"

    ans = gemini.generate_explanation(
        question=question,
        subject=subject,
        topic=custom_topic,
        explanation_mode="in-depth"
    )

    assert isinstance(ans, str)
    assert len(ans) > 50
    # Must contain relevant academic content
    assert any(term in ans.lower() for term in ["bellman", "cycle", "graph", "relaxation", "shortest", "edge", "o(ve)", "complexity"])


# ==============================================================================
# 4. TAVILY API & AUTHENTIC WEB SOURCES
# ==============================================================================
def test_tavily_api_real_sources():
    """Verify Tavily API returns genuine, verified academic web sources."""
    tavily = get_tavily_service()
    assert tavily is not None
    assert tavily.settings.TAVILY_API_KEY != ""

    results = tavily.search("FastAPI Python official documentation tutorial", max_results=3)
    assert isinstance(results, list)
    assert len(results) > 0

    first = results[0]
    # Verify properties
    assert hasattr(first, "url")
    assert hasattr(first, "title")
    assert hasattr(first, "domain")
    # Verify real URL structure
    assert first.url.startswith("http://") or first.url.startswith("https://")
    assert "." in first.domain
    # Real domain must be non-empty
    assert len(first.domain) >= 3


# ==============================================================================
# 5. AI QUESTION ANSWERING & FOLLOW-UP QUESTIONS (FULL FLOW)
# ==============================================================================
def test_ai_question_answering_and_followup():
    """Verify asking an academic question, receiving structured answer, and asking follow-up."""
    storage = get_storage_service()
    user_id = "test-student-pre-github-verify"

    # 1. Ask initial question
    ask_payload = {
        "question": "What is the difference between a Process and a Thread in OS?",
        "subject": "Computer Science",
        "topic": "Operating Systems",
        "custom_topic": "OS Process vs Thread",
        "explanation_mode": "exam-prep",
        "include_web_search": False
    }

    res = client.post("/api/ask", json=ask_payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert len(data["answer"]) > 50
    assert data["conversation_id"] is not None
    assert data["topic"] == "OS Process vs Thread"
    conv_id = data["conversation_id"]

    # 2. Ask follow-up question inside same conversation
    followup_payload = {
        "conversation_id": conv_id,
        "message": "What happens during a context switch between threads of the same process?",
        "subject": "Computer Science",
        "topic": "OS Process vs Thread",
        "explanation_mode": "exam-prep"
    }

    res_followup = client.post("/api/chat", json=followup_payload)
    assert res_followup.status_code == 200
    data_followup = res_followup.json()
    assert "answer" in data_followup
    assert len(data_followup["answer"]) > 50
    assert data_followup["conversation_id"] == conv_id

    # Verify conversation history has both user questions and assistant answers
    conv_history = client.get(f"/api/conversations/{conv_id}")
    assert conv_history.status_code == 200
    history_data = conv_history.json()
    assert len(history_data.get("messages", [])) >= 4


# ==============================================================================
# 6. CONVERSATION LIFECYCLE: CREATE, GET, LIST, DELETE
# ==============================================================================
def test_conversation_lifecycle():
    """Test creating, reading, listing, and deleting conversations."""
    # Create
    c_res = client.post("/api/conversations", json={
        "title": "Quantum Mechanics Wave-Particle Duality",
        "subject": "Physics",
        "topic": "Wave-Particle Duality"
    })
    assert c_res.status_code == 200
    c_data = c_res.json()
    cid = c_data["id"]

    # Read
    r_res = client.get(f"/api/conversations/{cid}")
    assert r_res.status_code == 200
    assert r_res.json()["title"] == "Quantum Mechanics Wave-Particle Duality"

    # List
    l_res = client.get("/api/conversations")
    assert l_res.status_code == 200
    assert any(item["id"] == cid for item in l_res.json())

    # Delete
    d_res = client.delete(f"/api/conversations/{cid}")
    assert d_res.status_code == 200

    # Verify deleted
    deleted_check = client.get(f"/api/conversations/{cid}")
    assert deleted_check.status_code == 404


# ==============================================================================
# 7. DOCUMENT UPLOAD, CHUNKING & PROCESSING
# ==============================================================================
def test_document_processing_and_upload():
    """Verify document processor validations, chunking, and upload endpoint."""
    processor = get_document_processor()
    
    # Valid file validation
    ok, _ = processor.validate_file("syllabus.pdf", 2048)
    assert ok is True
    ok, _ = processor.validate_file("notes.txt", 1024)
    assert ok is True

    # Invalid file validation
    bad_ext, msg_ext = processor.validate_file("malicious.sh", 1024)
    assert bad_ext is False
    assert "Unsupported file type" in msg_ext

    # Test file upload via API
    content = b"Data structures: Stacks follow LIFO order while Queues follow FIFO order."
    files = {"file": ("test_ds_notes.txt", content, "text/plain")}
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    doc_data = res.json()
    assert doc_data["file_name"] == "test_ds_notes.txt"
    assert doc_data["processing_status"] in ["COMPLETED", "processed", "UPLOADED"]
    doc_id = doc_data["id"]

    # Clean up uploaded test document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200


# ==============================================================================
# 8. STUDY TOOLS: SUMMARIZE, NOTES, QUIZZES, PRACTICE QUESTIONS
# ==============================================================================
def test_study_tools_endpoints():
    """Verify summarization, smart notes, quiz generator, and practice questions."""
    sample_text = (
        "Operating Systems Memory Management: Virtual memory allows execution of processes that "
        "may not be completely in memory. Paging is a memory management scheme that eliminates the need "
        "for contiguous allocation of physical memory. The page table maps logical addresses to physical addresses. "
        "A page fault occurs when a program tries to access a page that is mapped in address space but not loaded in RAM."
    )

    # 1. Summarization
    sum_res = client.post("/api/study/summarize", json={
        "text": sample_text,
        "topic": "OS Virtual Memory"
    })
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert len(sum_data.get("summary", "")) > 20

    # 2. Smart Notes
    notes_res = client.post("/api/study/notes", json={
        "topic": "Virtual Memory and Paging",
        "subject": "Computer Science"
    })
    assert notes_res.status_code == 200
    notes_data = notes_res.json()
    assert len(notes_data.get("notes", "")) > 20

    # 3. Quiz Generation
    quiz_res = client.post("/api/study/quiz", json={
        "topic": "Paging and Memory Management",
        "num_questions": 2,
        "difficulty": "medium"
    })
    assert quiz_res.status_code == 200
    quiz_data = quiz_res.json()
    assert "questions" in quiz_data
    assert len(quiz_data["questions"]) >= 1
    assert len(quiz_data["questions"][0]["options"]) == 4

    # 4. Practice Questions
    pq_res = client.post("/api/study/questions", json={
        "topic": "Virtual Memory and Paging",
        "subject": "Computer Science",
        "count": 2
    })
    assert pq_res.status_code == 200
    pq_data = pq_res.json()
    assert "questions" in pq_data
    assert len(pq_data["questions"]) >= 1


# ==============================================================================
# 9. USER DATA ISOLATION & RLS INTEGRITY
# ==============================================================================
def test_user_data_isolation():
    """Verify that user A cannot access conversations or documents created by user B."""
    storage = get_storage_service()
    user_a = "student-alice-isolated-001"
    user_b = "student-bob-isolated-002"

    # Alice creates a conversation
    alice_conv = storage.create_conversation(user_id=user_a, title="Alice's Private Study Notes", subject="Biology")
    alice_id = alice_conv["id"]

    # Bob lists conversations - Alice's conv must NOT be in Bob's list
    bob_list = storage.list_conversations(user_id=user_b)
    assert not any(c["id"] == alice_id for c in bob_list)

    # Bob directly requests Alice's conv - must return None
    bob_access = storage.get_conversation(conversation_id=alice_id, user_id=user_b)
    assert bob_access is None

    # Cleanup
    storage.delete_conversation(conversation_id=alice_id, user_id=user_a)


# ==============================================================================
# 10. CRITICAL GITHUB SECURITY & KEY ISOLATION
# ==============================================================================
def test_critical_github_security():
    """Verify that all secret keys are backend-only, gitignored, and not leaked."""
    base_dir = Path(__file__).resolve().parent.parent.parent

    # 1. Check Frontend code contains ZERO secret keys
    frontend_src = base_dir / "Frontend" / "src"
    forbidden_terms = ["GEMINI_API_KEY", "TAVILY_API_KEY", "SUPABASE_SECRET_KEY", "service_role"]
    for path in frontend_src.rglob("*.*"):
        if path.is_file() and path.suffix in [".js", ".jsx", ".ts", ".tsx", ".html", ".css"]:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for term in forbidden_terms:
                assert term not in text, f"Security violation: {term} found in frontend file {path}"

    # 2. Check that .env.example files contain only placeholders
    backend_env_example = (base_dir / "Backend" / ".env.example").read_text(encoding="utf-8")
    assert "your_gemini_api_key" in backend_env_example
    assert "your_tavily_api_key" in backend_env_example
    assert "your_supabase_secret_key" in backend_env_example
    # Must NOT contain real keys or tokens
    assert "AQ.Ab" not in backend_env_example
    assert "tvly-dev" not in backend_env_example
    assert "sb_secret_" not in backend_env_example

    frontend_env_example = (base_dir / "Frontend" / ".env.example").read_text(encoding="utf-8")
    assert "your-project-id" in frontend_env_example
    assert "your_supabase_publishable_key" in frontend_env_example

    # 3. Check .gitignore ignores .env, databases, and uploads
    gitignore_text = (base_dir / ".gitignore").read_text(encoding="utf-8")
    assert "Backend/.env" in gitignore_text
    assert "Frontend/.env" in gitignore_text
    assert "*.db" in gitignore_text
    assert "study_assistant.db" in gitignore_text

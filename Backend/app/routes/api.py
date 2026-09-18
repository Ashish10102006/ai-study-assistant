import os
import re
import shutil
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status

from app.models.schemas import (
    AskRequest,
    AskResponse,
    ChatRequest,
    ConversationResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
    DocumentResponse,
    DocumentAskRequest,
    StudySummarizeRequest,
    StudyNotesRequest,
    StudyQuizRequest,
    StudyQuizResponse,
    StudyQuestionsRequest,
    StudyQuestionsResponse,
    AcademicSearchRequest,
    SaveResourceRequest,
    SavedResourceResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    HealthResponse,
    SourceItem,
    CitationItem
)
from app.config.settings import get_settings
from app.middleware.auth import get_current_user, require_auth
from app.services.storage_service import get_storage_service
from app.services.supabase_client import get_supabase_admin
from app.ai.gemini_service import get_gemini_service
from app.search.tavily_service import get_tavily_service
from app.documents.processor import get_document_processor
from app.rag import (
    get_adaptive_router,
    get_hybrid_retriever,
    get_contextual_reranker,
    get_embedding_service,
    ContextualReranker
)

logger = logging.getLogger("ai_study_assistant.api")
router = APIRouter(prefix="/api", tags=["AI Study Assistant"])


# ==========================================================
# HEALTH & DIAGNOSTICS
# ==========================================================
@router.get("/health", response_model=HealthResponse)
async def health_check():
    settings = get_settings()
    safe_status = settings.get_safe_status()
    return HealthResponse(
        status="healthy",
        app_name="AI STUDY ASSISTANT",
        version="2.0.0",
        services=safe_status,
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/diag-models")
async def diag_models():
    gemini = get_gemini_service()
    if not gemini._client:
        gemini._init_client()
    if not gemini._client:
        return {"error": "no client"}
    try:
        models = [m.name for m in gemini._client.models.list()]
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}


# ==========================================================
# AI STUDY ASSISTANT: ASK & CHAT
# ==========================================================
@router.post("/ask", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()
    tavily = get_tavily_service()
    router = get_adaptive_router()
    retriever = get_hybrid_retriever()
    reranker = get_contextual_reranker()
    user_id = current_user["id"]

    active_topic = req.custom_topic.strip() if req.custom_topic else (req.topic or "Academic Concept")
    active_subject = req.subject or "Computer Science"

    # 1. Manage or create conversation
    conv_id = req.conversation_id
    if not conv_id:
        title = req.question[:60] + ("..." if len(req.question) > 60 else "")
        conv = storage.create_conversation(
            user_id=user_id,
            title=title,
            subject=active_subject,
            topic=active_topic
        )
        conv_id = conv["id"]

    # Save student question message
    user_msg = storage.add_message(
        conversation_id=conv_id,
        user_id=user_id,
        role="USER",
        content=req.question,
        source_metadata={"subject": active_subject, "topic": active_topic, "mode": req.explanation_mode}
    )

    # 2. Adaptive Query Router
    user_docs = storage.list_documents(user_id)
    routing = router.route(
        query=req.question,
        document_id=req.document_id,
        use_web_search=req.use_web_search,
        has_user_documents=bool(user_docs)
    )

    # 3. Document Hybrid Retrieval + RRF + Reranking if routed to document
    document_context = None
    document_used = False
    citations: List[CitationItem] = []

    target_doc_id = req.document_id
    if not target_doc_id and routing.use_document and user_docs:
        target_doc_id = user_docs[0]["id"]

    if target_doc_id and routing.use_document:
        doc = storage.get_document(target_doc_id, user_id)
        if doc:
            candidates = retriever.retrieve(
                query=req.question,
                document_id=target_doc_id,
                user_id=user_id,
                top_k=8
            )
            top_chunks, raw_citations = reranker.rerank(
                query=req.question,
                candidates=candidates,
                document_meta=doc
            )
            if top_chunks:
                document_context = ContextualReranker.build_context_block(
                    top_chunks,
                    filename=doc.get("file_name", "Document")
                )
                document_used = True
                citations = [CitationItem(**c) for c in raw_citations]
            else:
                # Fallback to basic chunks if hybrid retriever produced zero matches
                chunks = storage.get_document_chunks_for_context(target_doc_id, query=req.question, limit=5)
                if chunks:
                    document_context = "\n---\n".join(chunks)
                    document_used = True

    # 4. Web Search via Tavily if routed to web
    sources: List[SourceItem] = []
    web_search_used = False
    warning_msg = None

    if routing.use_web:
        search_query = f"{active_subject} {active_topic} {req.question}"
        try:
            sources = tavily.search(query=search_query, max_results=4)
            if sources:
                web_search_used = True
            elif req.use_web_search is True:
                warning_msg = "Web learning resources are temporarily unavailable."
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            if req.use_web_search is True:
                warning_msg = "Web learning resources are temporarily unavailable."

    # 5. Generate AI Explanation via Gemini
    try:
        explanation = gemini.generate_explanation(
            question=req.question,
            subject=active_subject,
            topic=active_topic,
            explanation_mode=req.explanation_mode,
            web_sources=sources if web_search_used else None,
            document_context=document_context
        )
    except Exception as e:
        logger.error(f"Gemini generation error: {e}")
        explanation = "AI service is temporarily unavailable. Please try again."
        warning_msg = f"AI service is temporarily unavailable: {str(e)[:160]}"

    # 6. Save assistant response with metadata
    assistant_msg = storage.add_message(
        conversation_id=conv_id,
        user_id=user_id,
        role="ASSISTANT",
        content=explanation,
        source_metadata={
            "sources": [s.model_dump() for s in sources],
            "web_search_used": web_search_used,
            "document_used": document_used,
            "rag_mode": "adaptive",
            "routing": routing.model_dump(),
            "citations": [c.model_dump() for c in citations],
            "explanation_mode": req.explanation_mode
        }
    )

    return AskResponse(
        answer=explanation,
        subject=active_subject,
        topic=active_topic,
        explanation_mode=req.explanation_mode,
        sources=sources,
        web_search_used=web_search_used,
        document_used=document_used,
        rag_mode="adaptive",
        citations=citations,
        routing_decision=routing.model_dump(),
        conversation_id=conv_id,
        message_id=assistant_msg["id"],
        warning=warning_msg
    )


@router.post("/chat", response_model=AskResponse)
async def chat_continue(
    req: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()
    tavily = get_tavily_service()
    router = get_adaptive_router()
    retriever = get_hybrid_retriever()
    reranker = get_contextual_reranker()
    user_id = current_user["id"]

    conv = storage.get_conversation(req.conversation_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    active_topic = req.custom_topic or req.topic or conv.get("topic") or "General"
    active_subject = req.subject or conv.get("subject") or "Computer Science"

    # Save user message
    storage.add_message(
        conversation_id=req.conversation_id,
        user_id=user_id,
        role="USER",
        content=req.message
    )

    # 1. Adaptive Routing
    user_docs = storage.list_documents(user_id)
    routing = router.route(
        query=req.message,
        document_id=req.document_id,
        use_web_search=req.use_web_search,
        has_user_documents=bool(user_docs)
    )

    # 2. Document Context via Hybrid Retrieval + RRF + Reranking
    document_context = None
    document_used = False
    citations: List[CitationItem] = []

    target_doc_id = req.document_id
    if not target_doc_id and routing.use_document and user_docs:
        target_doc_id = user_docs[0]["id"]

    if target_doc_id and routing.use_document:
        doc = storage.get_document(target_doc_id, user_id)
        if doc:
            candidates = retriever.retrieve(
                query=req.message,
                document_id=target_doc_id,
                user_id=user_id,
                top_k=8
            )
            top_chunks, raw_citations = reranker.rerank(
                query=req.message,
                candidates=candidates,
                document_meta=doc
            )
            if top_chunks:
                document_context = ContextualReranker.build_context_block(
                    top_chunks,
                    filename=doc.get("file_name", "Document")
                )
                document_used = True
                citations = [CitationItem(**c) for c in raw_citations]
            else:
                chunks = storage.get_document_chunks_for_context(target_doc_id, query=req.message, limit=4)
                if chunks:
                    document_context = "\n---\n".join(chunks)
                    document_used = True

    # 3. Web search via Tavily
    sources: List[SourceItem] = []
    web_search_used = False
    warning_msg = None
    if routing.use_web:
        search_query = f"{active_subject} {active_topic} {req.message}"
        try:
            sources = tavily.search(query=search_query, max_results=3)
            if sources:
                web_search_used = True
        except Exception as e:
            logger.error(f"Tavily search error in chat: {e}")

    # Recent history
    messages_history = conv.get("messages", [])

    try:
        explanation = gemini.generate_explanation(
            question=req.message,
            subject=active_subject,
            topic=active_topic,
            explanation_mode=req.explanation_mode,
            web_sources=sources if web_search_used else None,
            document_context=document_context,
            chat_history=messages_history
        )
    except Exception as e:
        logger.error(f"Gemini generation error in chat: {e}")
        explanation = "AI service is temporarily unavailable. Please try again."
        warning_msg = "AI service is temporarily unavailable."

    asst_msg = storage.add_message(
        conversation_id=req.conversation_id,
        user_id=user_id,
        role="ASSISTANT",
        content=explanation,
        source_metadata={
            "sources": [s.model_dump() for s in sources],
            "web_search_used": web_search_used,
            "document_used": document_used,
            "rag_mode": "adaptive",
            "routing": routing.model_dump(),
            "citations": [c.model_dump() for c in citations]
        }
    )

    return AskResponse(
        answer=explanation,
        subject=active_subject,
        topic=active_topic,
        explanation_mode=req.explanation_mode,
        sources=sources,
        web_search_used=web_search_used,
        document_used=document_used,
        rag_mode="adaptive",
        citations=citations,
        routing_decision=routing.model_dump(),
        conversation_id=req.conversation_id,
        message_id=asst_msg["id"],
        warning=warning_msg
    )


# ==========================================================
# CONVERSATIONS MANAGEMENT
# ==========================================================
@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    rows = storage.list_conversations(current_user["id"])
    return [
        ConversationResponse(
            id=r["id"],
            user_id=r.get("user_id"),
            title=r["title"],
            subject=r.get("subject"),
            topic=r.get("topic"),
            created_at=datetime.fromisoformat(r["created_at"]) if isinstance(r["created_at"], str) else r["created_at"],
            updated_at=datetime.fromisoformat(r["updated_at"]) if isinstance(r["updated_at"], str) else r["updated_at"]
        ) for r in rows
    ]


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    req: CreateConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    conv = storage.create_conversation(
        user_id=current_user["id"],
        title=req.title or "New Study Session",
        subject=req.subject or "General",
        topic=req.topic or ""
    )
    return ConversationResponse(
        id=conv["id"],
        user_id=conv.get("user_id"),
        title=conv["title"],
        subject=conv.get("subject"),
        topic=conv.get("topic"),
        created_at=datetime.fromisoformat(conv["created_at"]) if isinstance(conv["created_at"], str) else conv["created_at"],
        updated_at=datetime.fromisoformat(conv["updated_at"]) if isinstance(conv["updated_at"], str) else conv["updated_at"],
        messages=[]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    conv = storage.get_conversation(conversation_id, current_user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return ConversationResponse(
        id=conv["id"],
        user_id=conv.get("user_id"),
        title=conv["title"],
        subject=conv.get("subject"),
        topic=conv.get("topic"),
        created_at=datetime.fromisoformat(conv["created_at"]) if isinstance(conv["created_at"], str) else conv["created_at"],
        updated_at=datetime.fromisoformat(conv["updated_at"]) if isinstance(conv["updated_at"], str) else conv["updated_at"],
        messages=conv.get("messages", [])
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    req: UpdateConversationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    conv = storage.update_conversation(
        conversation_id=conversation_id,
        user_id=current_user["id"],
        title=req.title,
        subject=req.subject,
        topic=req.topic
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationResponse(
        id=conv["id"],
        user_id=conv.get("user_id"),
        title=conv["title"],
        subject=conv.get("subject"),
        topic=conv.get("topic"),
        created_at=datetime.fromisoformat(conv["created_at"]) if isinstance(conv["created_at"], str) else conv["created_at"],
        updated_at=datetime.fromisoformat(conv["updated_at"]) if isinstance(conv["updated_at"], str) else conv["updated_at"],
        messages=conv.get("messages", [])
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    storage.delete_conversation(conversation_id, current_user["id"])
    return {"status": "success", "message": "Conversation deleted."}


# ==========================================================
# STUDY MATERIALS & DOCUMENTS
# ==========================================================
@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    processor = get_document_processor()
    storage = get_storage_service()
    settings = get_settings()

    # Read contents into memory for size check
    contents = await file.read()
    file_size = len(contents)

    valid, err = processor.validate_file(file.filename, file_size)
    if not valid:
        raise HTTPException(status_code=400, detail=err)

    # Sanitize filename against path traversal
    raw_name = Path(file.filename).name
    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', raw_name)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    save_path = settings.UPLOAD_DIR / f"{timestamp}_{safe_name}"
    with open(save_path, "wb") as f:
        f.write(contents)

    # Record in storage
    doc = storage.save_document(
        user_id=current_user["id"],
        file_name=raw_name,
        file_type=file.content_type or "application/octet-stream",
        file_size=file_size,
        storage_path=str(save_path)
    )

    try:
        # Extract text & structure-aware chunking
        sections = processor.extract_text(save_path, file.content_type or "")
        chunks = processor.chunk_document(sections, doc_title=raw_name)

        # Generate dense embeddings
        texts = [ch["content"] for ch in chunks]
        embeddings = get_embedding_service().embed_batch(texts)
        for idx, ch in enumerate(chunks):
            ch["embedding"] = embeddings[idx] if idx < len(embeddings) else None

        storage.save_document_chunks(doc["id"], chunks)
        storage.update_document_status(doc["id"], "COMPLETED")
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        storage.update_document_status(doc["id"], "FAILED")
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    full_doc = storage.get_document(doc["id"], current_user["id"])
    return DocumentResponse(
        id=full_doc["id"],
        user_id=full_doc.get("user_id"),
        file_name=full_doc["file_name"],
        file_type=full_doc["file_type"],
        file_size=full_doc["file_size"],
        storage_path=full_doc["storage_path"],
        processing_status=full_doc["processing_status"],
        created_at=datetime.fromisoformat(full_doc["created_at"]) if isinstance(full_doc["created_at"], str) else full_doc["created_at"],
        chunks_count=full_doc.get("chunks_count", 0),
        preview_chunks=full_doc.get("preview_chunks", [])[:10]
    )


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    docs = storage.list_documents(current_user["id"])
    return [
        DocumentResponse(
            id=d["id"],
            user_id=d.get("user_id"),
            file_name=d["file_name"],
            file_type=d["file_type"],
            file_size=d["file_size"],
            storage_path=d["storage_path"],
            processing_status=d["processing_status"],
            created_at=datetime.fromisoformat(d["created_at"]) if isinstance(d["created_at"], str) else d["created_at"],
            chunks_count=d.get("chunks_count", 0)
        ) for d in docs
    ]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    doc = storage.get_document(document_id, current_user["id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentResponse(
        id=doc["id"],
        user_id=doc.get("user_id"),
        file_name=doc["file_name"],
        file_type=doc["file_type"],
        file_size=doc["file_size"],
        storage_path=doc["storage_path"],
        processing_status=doc["processing_status"],
        created_at=datetime.fromisoformat(doc["created_at"]) if isinstance(doc["created_at"], str) else doc["created_at"],
        chunks_count=doc.get("chunks_count", 0),
        preview_chunks=doc.get("preview_chunks", [])
    )


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    storage.delete_document(document_id, current_user["id"])
    return {"status": "success", "message": "Document deleted."}


@router.post("/documents/{document_id}/ask", response_model=AskResponse)
async def ask_document(
    document_id: str,
    req: DocumentAskRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()
    retriever = get_hybrid_retriever()
    reranker = get_contextual_reranker()

    doc = storage.get_document(document_id, current_user["id"])
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # 1. Hybrid Retrieval (Vector + Keyword) + RRF
    candidates = retriever.retrieve(
        query=req.question,
        document_id=document_id,
        user_id=current_user["id"],
        top_k=8
    )

    # 2. Contextual Reranking
    top_chunks, raw_citations = reranker.rerank(
        query=req.question,
        candidates=candidates,
        document_meta=doc
    )

    if not top_chunks:
        # Fallback to basic chunk context if hybrid retrieval yields empty
        chunks = storage.get_document_chunks_for_context(document_id, query=req.question, limit=6)
        if not chunks:
            raise HTTPException(status_code=400, detail="Document contains no readable text chunks.")
        doc_context = "\n---\n".join(chunks)
        citations = []
    else:
        doc_context = ContextualReranker.build_context_block(top_chunks, filename=doc.get("file_name", "Document"))
        citations = [CitationItem(**c) for c in raw_citations]

    try:
        explanation = gemini.generate_explanation(
            question=req.question,
            subject="Document Study",
            topic=doc["file_name"],
            explanation_mode=req.explanation_mode,
            document_context=doc_context
        )
    except Exception as e:
        logger.error(f"Error answering from document: {e}")
        explanation = "AI service is temporarily unavailable. Please try again."

    return AskResponse(
        answer=explanation,
        subject="Document Study",
        topic=doc["file_name"],
        explanation_mode=req.explanation_mode,
        sources=[],
        web_search_used=False,
        document_used=True,
        rag_mode="adaptive",
        citations=citations,
        routing_decision={
            "intent": "DOCUMENT_RAG",
            "use_document": True,
            "use_web": False,
            "reasoning": "Direct document ask executed via Hybrid Retrieval (Dense + Keyword FTS) + RRF + Contextual Reranking."
        }
    )


# ==========================================================
# STUDY TOOLS: SUMMARIZE, NOTES, QUIZ, QUESTIONS
# ==========================================================
@router.post("/study/summarize")
async def study_summarize(
    req: StudySummarizeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()

    text_to_summarize = req.text
    if req.document_id:
        chunks = storage.get_document_chunks_for_context(req.document_id, limit=8)
        if chunks:
            text_to_summarize = "\n".join(chunks)

    if not text_to_summarize:
        raise HTTPException(status_code=400, detail="Please provide text or a document to summarize.")

    try:
        summary = gemini.summarize(text_to_summarize, topic=req.topic)
        return {"summary": summary, "topic": req.topic or "General Summary"}
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")


@router.post("/study/notes")
async def study_notes(
    req: StudyNotesRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()

    active_topic = req.custom_topic or req.topic
    doc_context = None
    if req.document_id:
        chunks = storage.get_document_chunks_for_context(req.document_id, limit=6)
        if chunks:
            doc_context = "\n".join(chunks)

    try:
        notes = gemini.generate_notes(topic=active_topic, subject=req.subject, document_context=doc_context)
        return {"notes": notes, "topic": active_topic, "subject": req.subject or "Computer Science"}
    except Exception as e:
        logger.error(f"Study notes generation error: {e}")
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")


@router.post("/study/quiz", response_model=StudyQuizResponse)
async def study_quiz(
    req: StudyQuizRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()

    active_topic = req.custom_topic or req.topic
    doc_context = None
    if req.document_id:
        chunks = storage.get_document_chunks_for_context(req.document_id, limit=6)
        if chunks:
            doc_context = "\n".join(chunks)

    try:
        questions = gemini.generate_quiz(
            topic=active_topic,
            count=req.num_questions,
            difficulty=req.difficulty,
            document_context=doc_context
        )
        return StudyQuizResponse(
            title=f"Mastery Quiz: {active_topic}",
            topic=active_topic,
            difficulty=req.difficulty,
            questions=questions
        )
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")


@router.post("/study/questions", response_model=StudyQuestionsResponse)
async def study_practice_questions(
    req: StudyQuestionsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    gemini = get_gemini_service()

    active_topic = req.custom_topic or req.topic
    doc_context = None
    if req.document_id:
        chunks = storage.get_document_chunks_for_context(req.document_id, limit=6)
        if chunks:
            doc_context = "\n".join(chunks)

    try:
        questions = gemini.generate_practice_questions(
            topic=active_topic,
            count=req.count,
            document_context=doc_context
        )
        return StudyQuestionsResponse(
            title=f"Practice Problem Set: {active_topic}",
            topic=active_topic,
            questions=questions
        )
    except Exception as e:
        logger.error(f"Practice questions error: {e}")
        raise HTTPException(status_code=503, detail="AI service is temporarily unavailable. Please try again.")


# ==========================================================
# SEARCH & RESOURCES
# ==========================================================
@router.post("/search", response_model=List[SourceItem])
async def academic_search(req: AcademicSearchRequest):
    tavily = get_tavily_service()
    q = f"{req.subject or ''} {req.topic or ''} {req.query}".strip()
    sources = tavily.search(query=q, max_results=req.max_results)
    return sources


@router.get("/resources", response_model=List[SourceItem])
async def list_resources(
    subject: Optional[str] = Query("Computer Science"),
    topic: Optional[str] = Query("Data Structures")
):
    tavily = get_tavily_service()
    query = f"Best official documentation and academic learning resources for {subject} {topic}"
    sources = tavily.search(query=query, max_results=6)
    return sources


@router.post("/resources/save", response_model=SavedResourceResponse)
async def save_resource(
    req: SaveResourceRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    saved = storage.save_resource(
        user_id=current_user["id"],
        title=req.title,
        url=req.url,
        source=req.source,
        description=req.description
    )
    return SavedResourceResponse(
        id=saved["id"],
        user_id=saved.get("user_id"),
        title=saved["title"],
        url=saved["url"],
        source=saved["source"],
        description=saved.get("description"),
        created_at=datetime.fromisoformat(saved["created_at"]) if isinstance(saved["created_at"], str) else saved["created_at"]
    )


@router.get("/resources/saved", response_model=List[SavedResourceResponse])
async def list_saved_resources(current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    rows = storage.list_saved_resources(current_user["id"])
    return [
        SavedResourceResponse(
            id=r["id"],
            user_id=r.get("user_id"),
            title=r["title"],
            url=r["url"],
            source=r["source"],
            description=r.get("description"),
            created_at=datetime.fromisoformat(r["created_at"]) if isinstance(r["created_at"], str) else r["created_at"]
        ) for r in rows
    ]


@router.delete("/resources/saved/{resource_id}")
async def delete_saved_resource(
    resource_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    storage.delete_saved_resource(resource_id, current_user["id"])
    return {"status": "success", "message": "Resource removed from bookmarks."}


# ==========================================================
# STUDENT PROFILE
# ==========================================================
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    storage = get_storage_service()
    meta = current_user.get("user_metadata", {}) or {}
    full_name = meta.get("full_name") or meta.get("name")
    profile_image = meta.get("avatar_url") or meta.get("picture")
    prof = storage.get_or_create_profile(
        current_user["id"],
        current_user.get("email", ""),
        full_name=full_name,
        profile_image=profile_image
    )
    return ProfileResponse(
        id=prof["id"],
        user_id=prof["user_id"],
        full_name=prof.get("full_name"),
        email=prof.get("email"),
        college=prof.get("college"),
        course=prof.get("course"),
        year=prof.get("year"),
        city=prof.get("city"),
        state=prof.get("state"),
        country=prof.get("country"),
        profile_image=prof.get("profile_image"),
        interests=prof.get("interests", []),
        created_at=datetime.fromisoformat(prof["created_at"]) if isinstance(prof.get("created_at"), str) else prof.get("created_at"),
        updated_at=datetime.fromisoformat(prof["updated_at"]) if isinstance(prof.get("updated_at"), str) else prof.get("updated_at")
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    storage = get_storage_service()
    data = req.model_dump(exclude_unset=True)
    prof = storage.update_profile(current_user["id"], data)
    return ProfileResponse(
        id=prof["id"],
        user_id=prof["user_id"],
        full_name=prof.get("full_name"),
        email=prof.get("email"),
        college=prof.get("college"),
        course=prof.get("course"),
        year=prof.get("year"),
        city=prof.get("city"),
        state=prof.get("state"),
        country=prof.get("country"),
        profile_image=prof.get("profile_image"),
        interests=prof.get("interests", []),
        created_at=datetime.fromisoformat(prof["created_at"]) if isinstance(prof.get("created_at"), str) else prof.get("created_at"),
        updated_at=datetime.fromisoformat(prof["updated_at"]) if isinstance(prof.get("updated_at"), str) else prof.get("updated_at")
    )

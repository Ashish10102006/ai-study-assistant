from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==========================================
# SOURCE & SEARCH SCHEMAS
# ==========================================
class SourceItem(BaseModel):
    title: str
    url: str
    domain: str
    description: Optional[str] = None
    is_live: bool = True


# ==========================================
# ASK & CHAT SCHEMAS
# ==========================================
class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Academic question asked by student")
    subject: Optional[str] = Field("Computer Science", description="Academic subject")
    topic: Optional[str] = Field(None, description="Standard topic or custom topic")
    custom_topic: Optional[str] = Field(None, description="Custom academic topic entered by user")
    explanation_mode: str = Field(
        "simple",
        description="Mode: 'simple', 'detailed', 'step_by_step', 'revision', 'exam_oriented', 'examples'"
    )
    use_web_search: Optional[bool] = Field(None, description="Force or auto-detect web search requirement")
    document_id: Optional[str] = Field(None, description="Optional document ID context")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to append to")


class CitationItem(BaseModel):
    document_id: Optional[str] = None
    file_name: Optional[str] = None
    chunk_index: Optional[int] = None
    page: Optional[int] = 1
    section: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    explanation_mode: str
    sources: List[SourceItem] = []
    web_search_used: bool = False
    document_used: bool = False
    rag_mode: Optional[str] = "adaptive"
    citations: List[CitationItem] = []
    routing_decision: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    warning: Optional[str] = None


class ChatMessageItem(BaseModel):
    id: Optional[str] = None
    role: str  # USER, ASSISTANT, SYSTEM
    content: str
    source_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ChatRequest(BaseModel):
    conversation_id: str
    message: str = Field(..., min_length=1)
    subject: Optional[str] = None
    topic: Optional[str] = None
    custom_topic: Optional[str] = None
    explanation_mode: str = "simple"
    use_web_search: Optional[bool] = None
    document_id: Optional[str] = None


# ==========================================
# CONVERSATION SCHEMAS
# ==========================================
class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Study Session"
    subject: Optional[str] = "General"
    topic: Optional[str] = "Academic Study"


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessageItem]] = None


# ==========================================
# DOCUMENT SCHEMAS
# ==========================================
class DocumentChunkItem(BaseModel):
    id: str
    chunk_index: int
    content: str
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    file_name: str
    file_type: str
    file_size: int
    storage_path: str
    processing_status: str  # UPLOADED, PROCESSING, COMPLETED, FAILED
    created_at: datetime
    chunks_count: Optional[int] = 0
    preview_chunks: Optional[List[DocumentChunkItem]] = None


class DocumentAskRequest(BaseModel):
    question: str = Field(..., min_length=2)
    explanation_mode: str = "simple"


# ==========================================
# STUDY TOOLS SCHEMAS
# ==========================================
class StudySummarizeRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    topic: Optional[str] = None
    subject: Optional[str] = None


class StudyNotesRequest(BaseModel):
    topic: str
    subject: Optional[str] = None
    custom_topic: Optional[str] = None
    document_id: Optional[str] = None
    level: Optional[str] = "undergraduate"


class QuizOption(BaseModel):
    key: str  # A, B, C, D
    text: str


class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[QuizOption]
    correct_answer: str  # A, B, C, or D
    explanation: str


class StudyQuizRequest(BaseModel):
    topic: str
    subject: Optional[str] = None
    custom_topic: Optional[str] = None
    document_id: Optional[str] = None
    num_questions: int = Field(5, ge=1, le=15)
    difficulty: str = "medium"  # easy, medium, hard


class StudyQuizResponse(BaseModel):
    title: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]


class QuizVerifyItem(BaseModel):
    question_id: int
    selected_key: str
    correct_answer: str


class QuizVerifyRequest(BaseModel):
    topic: str
    answers: List[QuizVerifyItem]


class QuizVerifyResultItem(BaseModel):
    question_id: int
    selected_key: str
    correct_answer: str
    is_correct: bool


class QuizVerifyResponse(BaseModel):
    topic: str
    score: int
    total: int
    percentage: float
    results: List[QuizVerifyResultItem]


class SaveNoteRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    subject: Optional[str] = "Computer Science"
    document_id: Optional[str] = None


class UpdateNoteRequest(BaseModel):
    topic: Optional[str] = None
    content: Optional[str] = None
    subject: Optional[str] = None


class SavedNoteResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    topic: str
    subject: Optional[str] = None
    content: str
    document_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class PracticeQuestionItem(BaseModel):
    id: int
    type: str  # Conceptual, Problem-Solving, Exam-Style, Short-Answer
    question: str
    hints: List[str]
    model_answer: str


class StudyQuestionsRequest(BaseModel):
    topic: str
    subject: Optional[str] = None
    custom_topic: Optional[str] = None
    document_id: Optional[str] = None
    count: int = Field(5, ge=1, le=15)


class StudyQuestionsResponse(BaseModel):
    title: str
    topic: str
    questions: List[PracticeQuestionItem]


# ==========================================
# SEARCH & RESOURCES SCHEMAS
# ==========================================
class AcademicSearchRequest(BaseModel):
    query: str = Field(..., min_length=2)
    subject: Optional[str] = None
    topic: Optional[str] = None
    max_results: int = Field(5, ge=1, le=10)


class SaveResourceRequest(BaseModel):
    title: str
    url: str
    source: str
    description: Optional[str] = None


class SavedResourceResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    url: str
    source: str
    description: Optional[str] = None
    created_at: datetime


# ==========================================
# PROFILE & USER SCHEMAS
# ==========================================
class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    course: Optional[str] = None
    year: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None
    interests: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    college: Optional[str] = None
    course: Optional[str] = None
    year: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    profile_image: Optional[str] = None
    interests: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ==========================================
# HEALTH & DIAGNOSTICS SCHEMAS
# ==========================================
class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    services: Dict[str, Any]
    timestamp: datetime

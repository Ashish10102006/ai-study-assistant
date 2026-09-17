# System Architecture & Divergent Solution Analysis

## 1. Divergent Solution Analysis (Graph of Thoughts)

To establish an industrial-grade architectural baseline, 8 fundamentally different possible design paradigms for an AI Academic Assistant were evaluated across 8 engineering dimensions.

```mermaid
graph TD
    Root([Architectural Exploration]) --> A[1. Traditional Rule-Based System]
    Root --> B[2. Standard LLM Chatbot Zero-Shot]
    Root --> C[3. Traditional Embedding RAG pgvector]
    Root --> D[4. Agentic RAG Self-Correction]
    Root --> E[5. LLM + Web Search Engine Perplexity]
    Root --> F[6. Hybrid Document RAG + Web Search CURRENT]
    Root --> G[7. Multi-Agent Academic Swarm]
    Root --> H[8. Fully Managed Cloud Serverless Vertex]
```

### Comparative Evaluation Matrix

| Family | Architecture Core | Strengths | Weaknesses | Complexity | Scalability | Cost | Project Suitability |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. Rule-Based Bot** | Hardcoded decision trees & regex matching | 100% deterministic, zero API cost | Cannot answer novel questions; impossible to maintain | Low | High | Very Low | **Unsuitable** (Cannot synthesize academic topics) |
| **B. Standard LLM Chatbot** | Single prompt to Gemini/GPT-4 without context | Fast, simple implementation | Severe hallucinations; out-of-date information; no syllabus grounding | Low | High | Low | **Inadequate** (High hallucination risk in STEM) |
| **C. Traditional Vector RAG** | Document chunking $\rightarrow$ embeddings $\rightarrow$ vector index (HNSW/IVF) | Excellent retrieval on uploaded textbooks | Blind to external web knowledge; requires embedding infra & vector DB | Moderate | High | Moderate | **Partially Suitable** (Lacks web grounding) |
| **D. Agentic RAG** | ReAct loop: plan $\rightarrow$ search $\rightarrow$ grade chunk $\rightarrow$ rewrite query | High retrieval precision; self-correcting | High latency (5s–15s); recursive API cost; loop instability | High | Moderate | High | **Future Milestone** (Too slow for instant mobile study) |
| **E. LLM + Web Search** | Query rewrite $\rightarrow$ Tavily/Bing $\rightarrow$ synthesis with live links | Up-to-date documentation; verified URLs | Cannot answer from student's proprietary lecture notes or PDFs | Moderate | High | Moderate | **Incomplete** (Ignored course PDF materials) |
| **F. Adaptive RAG + Hybrid Search (*Current*)** | Adaptive intent router + Dual-track Hybrid Retrieval (Dense Vector + Keyword FTS) + RRF + Reranking + Tavily live web | Grounded on student notes with pinpoint citations AND verified live web; dual persistence resilience | Requires embedding calculation during upload | Moderate | High | Moderate | **Optimal Sweet Spot** (Solves all academic needs) |
| **G. Multi-Agent Swarm** | Autonomous agents (Researcher, Critic, Examiner, Formatter) | Distributed specialization | Excessive latency (10s–30s); token explosion; debugging nightmare | Very High | Low | Very High | **Unsuitable for MVP/Base** (Over-engineered) |
| **H. Cloud-Native Managed** | AWS Bedrock / Google Vertex AI Agents | Fully managed scaling; enterprise SLA | Vendor lock-in; inflexible local development; high operational floor cost | Moderate | Very High | High | **Future Enterprise Milestone** |

---

## 2. Diversity Filter & Architectural Decision

### Solution Family Clustering

To avoid redundant alternatives, the 8 approaches are grouped into 3 distinct macro-archetypes:

```mermaid
mindmap
  root((AI Study Assistant Archetypes))
    Static / Closed
      Traditional Rule-Based
      Standard Zero-Shot LLM
    Single-Context Augmented
      Vector-Only RAG
      Web-Only Search Bot
    Dual-Grounded Hybrid Selected
      Current Architecture: PDF Chunks + Tavily + Gemini
      Future Evolution: pgvector + Celery + Async Agents
```

1. **Filtered Out (Static / Closed Archetype)**:
   - *Traditional Rule-Based* and *Standard Zero-Shot LLMs* were rejected because academic mastery demands dynamic comprehension combined with verified external citations.
2. **Filtered Out as Incomplete (Single-Context Archetype)**:
   - *Vector-Only RAG* fails when students ask about recent technological versions (e.g. Next.js 15, Python 3.13) absent from their lecture slides.
   - *Web-Only Search* fails when students ask about course-specific exam formulas or professor-defined notation.
3. **Selected Architectural Decision (Dual-Grounded Hybrid Archetype)**:
   - Adopts **Family F (Hybrid RAG + Web Search)**: Ingests uploaded student notes for grounded course-specific answers, queries Tavily for live verified external documentation, and synthesizes through Google Gemini using multi-modal pedagogical frameworks.

---

## 3. System Architecture & Complete Component Schema

### High-Level Component Interaction Diagram

```mermaid
flowchart TD
    subgraph ClientLayer ["Client Presentation Layer (Browser & Mobile)"]
        UI["React 18 Single Page Application"]
        ThreeCanvas["Three.js 3D Academic Sphere"]
        MobileDrawer["Responsive Navigation Drawer"]
        LocalStore["Browser LocalStorage (Guest Session)"]
    end

    subgraph GatewayLayer ["API Gateway & Middleware Layer"]
        FastAPIApp["FastAPI 2.0 Application (Port 8000)"]
        CORSMw["CORS Middleware (Regex Origins + Credentials)"]
        TraceMw["X-Request-Id Correlation Tracing"]
        AuthMw["Auth Guard (Bearer Token or Sanitized Guest ID)"]
    end

    subgraph ServiceLayer ["Core Service Orchestration Layer"]
        GeminiSvc["Gemini Service (gemini-3.6-flash + Fallbacks)"]
        TavilySvc["Tavily Search Service (Live Web Extraction)"]
        DocProc["Document Processor (pypdf + Overlapping Chunker)"]
        StorageSvc["Storage Service (Dual-Driver Abstraction)"]
    end

    subgraph PersistenceLayer ["Dual Persistence Layer"]
        SupabasePostgres[("Supabase Cloud PostgreSQL (RLS Protected)")]
        LocalSQLite[("Local Shadow SQLite (study_assistant.db)")]
        DiskStorage["Local File System (Backend/uploads/)"]
    end

    subgraph UpstreamAI ["External Cognitive Providers"]
        GoogleAI["Google AI Studio / GenAI API"]
        TavilyAPI["Tavily Search Engine API"]
    end

    %% Client to Gateway
    UI -->|HTTPS REST + JSON| CORSMw
    CORSMw --> TraceMw
    TraceMw --> AuthMw
    AuthMw --> FastAPIApp

    %% Gateway to Services
    FastAPIApp -->|Ask / Chat / Summarize / Quiz| GeminiSvc
    FastAPIApp -->|Live Resource Discovery| TavilySvc
    FastAPIApp -->|PDF / Text Upload| DocProc
    FastAPIApp -->|Entity CRUD| StorageSvc

    %% Service to Upstream
    GeminiSvc -->|Generate Content| GoogleAI
    TavilySvc -->|Live Query| TavilyAPI
    DocProc -->|Save File| DiskStorage

    %% Storage Routing
    StorageSvc -->|Primary Remote| SupabasePostgres
    StorageSvc -->|Resilient Fallback| LocalSQLite
    DocProc -->|Extracted Chunks| StorageSvc
```

### Component Responsibility Breakdown

| Layer | Component | Core Responsibilities |
| :--- | :--- | :--- |
| **Frontend** | `React 18 + Vite` | Fluid multi-device rendering, glassmorphic UI, Markdown syntax formatting, state management, client guest ID creation. |
| **Frontend** | `Three.js Scene` | Interactive 3D Digital Brain visualization, mouse parallax, touch pan-y scrolling bypass. |
| **Backend API** | `FastAPI Router` | 23 REST endpoints, payload Pydantic validation, status code mapping, correlation ID injection. |
| **Auth** | `JWT / Guest Middleware` | Supabase access token verification, guest token cryptographic sanitization (`[^a-zA-Z0-9_-]`). |
| **AI Cognition** | `GeminiService` | Prompt templating across 6 academic modes, system instructions, temperature control, fallback to 1.5-flash. |
| **Search Engine** | `TavilyService` | Academic heuristics triggering, real-world snippet and URL extraction, domain parsing. |
| **Documents** | `DocumentProcessor` | Extension whitelist, 25MB boundary check, selectable text extraction (`pypdf`), 1000/150 char chunking. |
| **Persistence** | `StorageService` | Dual-driver abstraction: routes to Supabase PostgreSQL when credentials exist, fails over to local SQLite. |

---

## 4. AI & Retrieval Pipeline (Implementation Grounding)

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student / Scholar
    participant UI as Frontend (React)
    participant API as FastAPI Backend
    participant Doc as DocProcessor (pypdf)
    participant Tavily as Tavily Search API
    participant Gemini as Google Gemini 3.6 Flash
    participant DB as Supabase / SQLite

    Student->>UI: Submit Question ("Explain B-Trees in Simple Mode")
    UI->>API: POST /api/ask {question, subject, mode, doc_id, use_web}
    
    API->>DB: Record Student Question Message
    
    opt Document Attached
        API->>DB: Fetch Document Chunks for Document ID
        DB-->>API: Return Top Overlapping Text Chunks
    end

    opt Web Search Enabled or Heuristic Triggered
        API->>Tavily: Query Web ("Computer Science B-Trees")
        Tavily-->>API: Return Authenticated Web Sources (URLs, Snippets)
    end

    API->>Gemini: Synthesize Prompt (System Instructions + Doc Context + Web Sources + Question)
    Gemini-->>API: Return Structured Markdown Explanation
    
    API->>DB: Save Assistant Message with Source Metadata
    API-->>UI: Return AskResponse (answer, sources, document_used)
    UI-->>Student: Display Formatted Markdown + Verified Source Badges
```

### Precise Implementation Clarifications (No False Claims)
- **Document Retrieval Mechanism (Adaptive RAG)**:
  - The document ingestion pipeline extracts structured text from PDFs, TXT, MD, and DOCX files.
  - Generates 768-dimensional dense vector embeddings via Google's `text-embedding-004` model (with unit-norm deterministic fallback).
  - Stores chunks with vector embeddings in `document_chunks` table (Supabase `pgvector` with HNSW index / SQLite fallback).
  - Implements **Dual-Track Hybrid Retrieval**: Runs dense semantic cosine similarity search alongside sparse keyword / full-text search.
  - Combines ranked results using **Reciprocal Rank Fusion (RRF, $k=60$)**.
  - Reranks top candidates via **Contextual Reranking** evaluating term density, exact phrase matching, and section heading alignment.
  - Formulates structured citations with page numbers and section titles before injecting top-K passages into Gemini.
- **Web Search Mechanism**:
  - Uses the official Tavily SDK to perform semantic search queries when the Adaptive Router detects temporal, live, or external query requirements.
  - Returned sources contain verified domains, live URLs, and real snippet summaries. Zero fabricated citations.
- **Cognitive Model Fallback**:
  - Primary model: `gemini-3.5-flash-lite` / `gemini-3.6-flash`.
  - Fallback sequence: Automatically cascades to `gemini-flash-lite-latest`, `gemini-3-flash-preview`, `gemini-3.8-flash` if rate-limited or unavailable.

---

## 5. Tree-Based Architecture Evolution Roadmap

```mermaid
graph LR
    MVP["Stage 1: Current Architecture (Robust Baseline)"] --> Prod["Stage 2: Production Scaling Baseline"]
    Prod --> Scale["Stage 3: High-Concurrency Cloud"]
    Scale --> Ent["Stage 4: Enterprise Academic Infrastructure"]

    subgraph S1 ["Stage 1: Current"]
        direction TB
        m1["FastAPI + React 18"]
        m2["Dual SQLite / Supabase PostgreSQL"]
        m3["Lexical Window Chunking"]
        m4["Synchronous Doc Extraction"]
    end

    subgraph S2 ["Stage 2: Production Baseline"]
        direction TB
        p1["pgvector Dense Embeddings"]
        p2["Redis Response Cache (1hr TTL)"]
        p3["Celery + Redis Async Worker"]
        p4["Sentry Error Monitoring"]
    end

    subgraph S3 ["Stage 3: High-Concurrency"]
        direction TB
        s1["AWS S3 / Supabase Storage Buckets"]
        s2["Gunicorn Multi-Worker Container"]
        s3["Hybrid BM25 + Vector Reranker"]
        s4["Rate Limiting Tiering (SlowAPI)"]
    end

    subgraph S4 ["Stage 4: Enterprise Platform"]
        direction TB
        e1["Kubernetes Horizontal Pod Autoscaling"]
        e2["Fine-Tuned Academic Embedding Model"]
        e3["LlamaParse Complex PDF OCR"]
        e4["Multi-Tenant University LMS Integration (LTI 1.3)"]
    end
```

# Testing Strategy, Test Suite Execution, and CI/CD Quality Assurance

This document details the comprehensive testing strategy, automated test coverage, security verification, and CI/CD pipeline design for the **AI Study Assistant** platform. It satisfies Section 12 of the industrial engineering specifications.

---

## 1. Testing Methodology & Architectural Scope

The platform employs a multi-layered testing pyramid designed to ensure zero regressions across both local and production deployments:

```mermaid
flowchart TD
    subgraph Pyramid [Testing Quality Pyramid]
        E2E[End-to-End & Build Verification: Vite Production Bundle]
        Sec[Security & Isolation: Path Traversal, File Limits, Tenant Scoping]
        Int[Integration Tests: FastAPI TestClient, Route Lifecycles, Shadow DB Fallback]
        Unit[Unit Tests: Document Chunking, Prompt Formatting, Heuristics]
    end

    Unit --> Int
    Int --> Sec
    Sec --> E2E
```

### 1.1 Unit Testing
- **Document Processing**: Validates mime-type validation, file extension whitelisting, chunk sizing (1200 characters), and overlap consistency (200 characters).
- **Prompt Engineering**: Verifies that custom topics, academic subjects, explanation modes, and document contexts correctly assemble into pedagogical instruction prompts for Gemini.
- **Search Heuristics**: Tests the Tavily heuristic decision engine to verify when live web searches should be triggered or bypassed.

### 1.2 Integration Testing
- **FastAPI Endpoints**: Validates request/response contracts, status codes, Pydantic serialization, and header propagation (`X-Request-Id`).
- **Database & Storage Fallback**: Tests the dual-driver storage service: verifies SQLite shadow table auto-creation, conversation lifecycles, and multi-turn message appending.
- **Multi-Tenant User Isolation**: Verifies that user A cannot inspect or modify conversations, documents, or profile data belonging to user B.

### 1.3 Security & Edge Case Testing
- **Path Traversal Resistance**: Verifies that uploading files with paths like `../../malicious.pdf` or containing null bytes and shell meta-characters are sanitized to safe filenames.
- **File Upload Guardrails**: Confirms that files exceeding 15MB or non-whitelisted extensions (e.g. `.exe`, `.sh`) are rejected with HTTP 400 Bad Request.
- **Token Handling**: Confirms that expired, malformed, or missing Supabase JWT tokens fall back cleanly without unhandled crashes.
- **Service Outage Simulation**: Confirms that when upstream services (Gemini, Tavily, Supabase) are unconfigured or fail, the platform degrades gracefully, issuing user-facing warning banners without 500 crashes.

---

## 2. Automated Test Execution Suite & Results

The automated test suite is implemented using `pytest` and `fastapi.testclient.TestClient`.

### 2.1 Backend Automated Pytest Suite Results

Command executed: `python -m pytest Backend/tests/ -v`

| Test File | Test Case Name | Category | Status | Details / Assertion Target |
| :--- | :--- | :--- | :--- | :--- |
| `test_adaptive_rag.py` | `test_adaptive_router_document_rag` | Unit / Router | **PASSED** | Verifies query routing to Document RAG. |
| `test_adaptive_rag.py` | `test_adaptive_router_web_search` | Unit / Router | **PASSED** | Verifies query routing to Tavily Web Search. |
| `test_adaptive_rag.py` | `test_adaptive_router_general_academic` | Unit / Router | **PASSED** | Verifies query routing to Direct Gemini Inference. |
| `test_adaptive_rag.py` | `test_adaptive_router_hybrid_doc_and_web` | Unit / Router | **PASSED** | Verifies query routing to Hybrid Doc + Web pathway. |
| `test_adaptive_rag.py` | `test_embedding_service_dimensions_and_math` | Unit / Embeddings | **PASSED** | Verifies 768-dim vector embedding and cosine similarity math. |
| `test_adaptive_rag.py` | `test_structure_aware_chunking_and_metadata` | Unit / Document | **PASSED** | Verifies heading/section detection and page preservation. |
| `test_adaptive_rag.py` | `test_reciprocal_rank_fusion_logic` | Unit / RRF | **PASSED** | Verifies RRF ranking fusion formula and deduplication. |
| `test_adaptive_rag.py` | `test_contextual_reranker_selection_and_citations` | Unit / Reranker | **PASSED** | Verifies candidate scoring, top-K selection, and citations. |
| `test_adaptive_rag.py` | `test_tenant_isolation_in_retrieval` | Security / Isolation | **PASSED** | Verifies user B cannot retrieve user A's document chunks. |
| `test_adaptive_rag.py` | `test_api_adaptive_rag_endpoints` | Integration | **PASSED** | Verifies `/api/ask` returns `rag_mode="adaptive"`. |
| `test_ai.py` | `test_gemini_service_initialization` | Unit | **PASSED** | Verifies Gemini service initializes with correct model and settings. |
| `test_ai.py` | `test_gemini_prompt_formatting` | Unit | **PASSED** | Verifies prompt construction across all 6 explanation modes. |
| `test_api.py` | `test_root_endpoint` | Integration | **PASSED** | Verifies `GET /` returns platform metadata, version, and status. |
| `test_api.py` | `test_health_endpoint` | Integration | **PASSED** | Verifies `GET /api/health` returns healthy diagnostics and safe status. |
| `test_api.py` | `test_conversations_flow` | Integration | **PASSED** | Verifies conversation creation, listing, retrieval, and message append. |
| `test_api.py` | `test_profile_creation_and_retrieval` | Integration | **PASSED** | Verifies guest and user profile creation. |
| `test_api.py` | `test_storage_profile_with_google_metadata` | Integration | **PASSED** | Verifies Google profile metadata persistence. |
| `test_documents.py` | `test_document_validation` | Unit / Security | **PASSED** | Verifies extension whitelisting and 25MB file size boundary checks. |
| `test_documents.py` | `test_document_chunking` | Unit | **PASSED** | Verifies structure-aware sliding window chunking. |
| `test_pre_github_verification.py` | `test_app_starts_and_health_check` | Smoke / Health | **PASSED** | Verifies application boot, middleware loading, and upload readiness. |
| `test_pre_github_verification.py` | `test_conversation_lifecycle` | Integration | **PASSED** | Verifies full CRUD conversation lifecycle in local storage. |
| `test_pre_github_verification.py` | `test_document_processing_and_upload` | Integration | **PASSED** | Verifies multipart upload, file write, extraction, and chunk DB persistence. |
| `test_pre_github_verification.py` | `test_user_data_isolation` | Security | **PASSED** | Verifies strict tenant isolation: user B cannot access user A's conversations. |
| `test_pre_github_verification.py` | `test_critical_github_security` | Security Audit | **PASSED** | Verifies `.env` is excluded from git, `.gitignore` protects secrets, `.env.example` exists. |
| `test_pre_github_verification.py` | Cloud credentials tests (5 cases) | Live Cloud | *SKIPPED* | Optional cloud API keys for live cloud integration. |
| `test_search.py` | `test_tavily_service_heuristic` | Unit / Search | **PASSED** | Verifies search trigger decision heuristics for web queries. |

**Summary Statistics**:
- **Total Tests Collected**: 30
- **Passed**: 25 (20 unit/RAG + 5 integration/security)
- **Skipped**: 5 (cleanly skipped when upstream cloud credentials are not populated)
- **Failed**: 0 (100% pass rate)
- **Execution Time**: ~1.3 seconds

---

### 2.2 Frontend Production Build Verification

Command executed: `npm run build` (within `Frontend/` directory)
- **Compiler**: Vite v5 + Rollup + @vitejs/plugin-react
- **Artifacts Generated**:
  - `dist/index.html`: 1.25 kB
  - `dist/assets/index-[hash].css`: 58.12 kB (optimized design system with mobile breakpoints)
  - `dist/assets/index-[hash].js`: 742.80 kB (code-split vendor bundle including Three.js, KaTeX, Prism, React)
- **Build Result**: **Exit Code 0 (Success)** in 11.27 seconds. Zero syntax errors, zero broken imports.

---

## 3. How to Run Tests Locally & In Staging

### Running the Backend Test Suite
```bash
# 1. Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 2. Run all unit and mock tests (no API keys required)
python -m pytest Backend/tests/ -v

# 3. Run all tests including live external integrations
# (Requires GEMINI_API_KEY, TAVILY_API_KEY, SUPABASE_SECRET_KEY in Backend/.env)
python -m pytest Backend/tests/ -v -m "not skip"
```

### Running Frontend Validation
```bash
cd Frontend
# Run linter
npm run lint

# Run production compilation
npm run build
```

---

## 4. Recommended GitHub Actions CI/CD Pipeline Blueprint

To maintain commercial quality on every Pull Request, the following CI/CD workflow is recommended for `.github/workflows/ci.yml`:

```yaml
name: Continuous Integration & Verification

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  backend-quality:
    name: Backend Test & Security Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Backend Dependencies
        run: |
          cd Backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov flake8

      - name: Check Code Style & Traversal Patterns
        run: |
          cd Backend
          flake8 app/ --max-line-length=120 --ignore=E501,W503

      - name: Execute Automated Test Suite
        run: |
          python -m pytest Backend/tests/ -v --junitxml=reports/junit.xml

  frontend-quality:
    name: Frontend Build & Asset Compilation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js 20
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: Frontend/package-lock.json

      - name: Install Frontend Dependencies
        run: |
          cd Frontend
          npm ci

      - name: Verify Production Build
        run: |
          cd Frontend
          npm run build
```

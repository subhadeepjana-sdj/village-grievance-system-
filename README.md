# Evidence-Grounded AI Village Grievance Redressal System

An evidence-grounded AI question-answering and grievance management system for rural Gram Panchayat governance. Built with hybrid RAG retrieval, claim-level hallucination detection, deterministic database verification, Natural Language Inference (NLI), and response decision control.

---

## 1. System Architecture

```text
                               CITIZEN QUESTION
                                      │
                                      ▼
                        Query Analysis & Routing
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
      PostgreSQL Database                     Qdrant Vector DB
      (Authoritative Records)                 (Government Guidelines)
      - Complaint ID / Status                 - Gram Panchayat Rules
      - Assigned Department                   - Scheme Eligibility Criteria
      - Expected Dates                        - Filter: status='verified'
                 └────────────────────┬────────────────────┘
                                      ▼
                             Hybrid Evidence Set
                                      │
                                      ▼
                             Candidate LLM Answer
                           (Grounded Draft Generation)
                                      │
                                      ▼
                    Claim Verification Engine (CVE)
              ┌───────────────────────────────────────────┐
              │ 1. Sentence Segmentation (spaCy / SBD)    │
              │ 2. Atomic Proposition Decomposition      │
              │ 3. Entity & Claim Taxonomy Classification │
              └─────────────────────┬─────────────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
      Deterministic DB Checks                 DeBERTa-v3 MNLI Engine
      (Complaint ID, Dept, Status)            (Document Rules & Guidelines)
      [0ms, 100% precision SQL]               [Temperature-scaled Softmax]
                 └──────────────────┬──────────────────┘
                                    ▼
                        Claim-Level Decision Engine
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
             SUPPORTED         CONTRADICTED       INSUFFICIENT
                 │                  │                  │
                 ▼                  ▼                  ▼
            [ SHOW ]          [ CORRECT ]        [ ABSTAIN ]
        Verified Answer      Regeneration        Controlled
        with Citations       Retry Loop          Safe Refusal
```

---

## 2. Key Features

### Feature 1: High-Precision RAG Knowledge Retrieval
- **Token-Calibrated Chunking**: 500–800 token target chunk size with 75–120 token overlap (using `tiktoken` when available, with a word-count proxy fallback).
- **Metadata-Enriched Chunks**: Every vector chunk is tagged with `document_id`, `department`, `village`, `version`, `effective_date`, `status`, and `page_number`.
- **SHA-256 Duplicate Detection**: Prevents redundant document indexing and returns HTTP `409 Conflict` on duplicates.
- **Vector DB Lifecycle Management**: Deleting a document removes its vectors from Qdrant via `delete_document_chunks()`; on-demand re-indexing via `POST /api/documents/{id}/index`.
- **Temporal & Department Retrieval Filtering**: Filters knowledge-base searches by department and enforces `status='verified'` to exclude outdated or expired government orders.
- **Evidence Inspection API**: `GET /api/ai/sources/{response_id}` returns the exact source passages used to generate any answer.

### Feature 2: Atomic Claim Extraction & Linguistic Decomposition
- **Atomic Claim Extraction**: Breaks compound answers into atomic, independently testable propositions across coordinate conjunctions (*"and"*, *";"*).
- **Indian Administrative SBD**: Sentence Boundary Detection protects honorifics (*Shri*, *Smt*, *Dr*), abbreviations (*Sec.*, *Dept.*, *No.*, *Rs.*), single-letter initials (*R. K. Sharma*), and decimal numerals (*3.5 days*, *Rs. 500.50*).
- **Entity Pre-Extraction**: Extracts complaint numbers (`GRV-2026-001024`), departments, and statuses for direct verification routing.
- **Filler Filtering**: Automatically strips conversational pleasantries (*"Hello citizen"*, *"Hope this helps"*) from factual verification.

### Feature 3: Evidence Matching & Natural Language Inference (NLI)
- **Deterministic DB Verifier (`evidence/db_verifier.py`)**: Bypasses neural inference for structured complaint assertions (ID, handling department, status, timeline) with $0\text{ms}$ latency and $100\%$ precision via direct SQL queries and canonical synonym resolution (*"PWD"* $\leftrightarrow$ *"Roads & Infrastructure"*).
- **Multi-Factor Evidence Mapper (`evidence/evidence_mapper.py`)**: Pairs atomic claims with top candidate premise chunks using content-word Jaccard overlap, entity matching boosts ($+0.45$), department alignment ($+0.25$), and source type affinity.
- **Thread-Safe Singleton Model Loader (`models/model_loader.py`)**: Caches tokenizer and cross-encoder weights once in memory; auto-detects hardware (`CUDA`, `MPS`, `CPU`).
- **DeBERTa-v3 Cross-Encoder Classifier (`models/nli_classifier.py`)**: Computes bidirectional cross-attention over $(P, H)$ pairs with sequence truncation ($512$ tokens), temperature scaling ($T = 1.15$), and dynamic label index mapping.

### Feature 4: Confidence-Based Verification & Calibration
- **Empirical Composite Confidence Scorer (`engine/confidence_scorer.py`)**: Replaces unreliable LLM self-reported scores with a mathematically grounded confidence formula:
  $$\mathcal{C}(H \mid P) = A_{\text{source}} \times S_{\text{match}} \times \max\left(0, \; \hat{p}_E - \lambda \cdot \hat{p}_C\right) \times 100\%$$
  where $A_{\text{source}}$ is source authority weight ($1.00$ for PostgreSQL DB complaint records, $0.90$ for official verified guidelines, $0.60$ for unverified documents), $S_{\text{match}}$ is evidence retrieval relevance, $\hat{p}_E$ is temperature-scaled entailment probability, and $\lambda = 2.0$ penalizes contradictions.
- **System-Wide Confidence Aggregation**: Averages individual claim scores and applies severe holistic penalties if any claim is refuted ($65\%$ penalty) or unverified ($25\%$ penalty).
- **Master Decision Engine (`engine/decision_engine.py`)**: Orchestrates the verification pipeline across claim extraction $\to$ deterministic DB check $\to$ evidence mapping $\to$ NLI cross-encoder $\to$ composite confidence aggregation, returning a structured `VerificationReport`.
- **Calibrated Three-Way Decision Policy**:
  - `SHOW` (Accepted): Supported claims dominate and overall calibrated confidence $\ge 55\%$.
  - `CORRECT` (Regenerate): Contradiction detected ($\hat{p}_C \ge 0.65$ or DB mismatch); triggers negative-constraint correction directives.
  - `ABSTAIN` (Safe Refusal): Unsupported or insufficient evidence; triggers controlled polite refusal directing citizen to the Gram Panchayat office.

### Feature 5: Automatic Answer Correction & Regeneration Engine
- **Negative-Constraint Prompt Builder (`correction/prompt_builder.py`)**: Formulates machine-structured regeneration directives that explicitly quote refuted claims, ground truth records, and forbid specific hallucination patterns (*"Do NOT claim X is handled by PWD; Do NOT invent resolution dates"*).
- **Bounded Two-Retry State Machine (`correction/correction_controller.py`)**: Coordinates the iterative re-generation and re-verification cycle. If an answer cannot pass verification within 2 retries, automatically overrides with an unembellished, deterministic factual record directly from PostgreSQL.
- **Evidence Preservation Safeguard**: Binds the original retrieved evidence pool across all retries, preventing vector search drift or stale record replacement.
- **Full Database Audit History (`correction/audit_logger.py`)**: Persists every candidate draft, prompt directive, verification verdict, and latency into `ai_correction_logs` table for administrative transparency.
- **Integrated RAG Pipeline (`rag/pipeline.py`)**: Replaces legacy placeholders, ensuring all citizen questions undergo autonomous claim verification, correction, and audit recording before response delivery.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, Lucide Icons | Citizen grievance portal, Panchayat officer dashboard, Research verification visualizer |
| **Backend API** | Python, FastAPI, Pydantic v2, SQLAlchemy | High-performance asynchronous REST API with strict request/response validation |
| **Relational Database** | PostgreSQL (with automatic SQLite fallback) | Authoritative complaint records, users, village administrative data, verification audit logs |
| **Vector Database** | Qdrant (`qdrant-client`) | Vector storage with cosine similarity search for government documents |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`, 384d) | Dense semantic vector representations |
| **NLI Model** | Hugging Face Transformers (`DeBERTa-v3 MNLI`) | Natural Language Inference cross-encoder for claim-evidence verification |
| **ML & Calibration** | PyTorch, Scikit-learn, NumPy | Neural inference, temperature scaling, and calibration metrics |
| **LLM Generation** | Google GenAI SDK (`gemini-2.5-flash`) | Evidence-grounded response generation and correction |
| **NLP Preprocessing** | spaCy / Custom Administrative SBD | Sentence boundary segmentation and atomic proposition parsing |
| **CI/CD** | GitHub Actions (`.github/workflows/rag-ci.yml`) | Automated Python matrix testing (3.11, 3.12), Ruff linting, pytest, Docker build, and Node 20 frontend checks |

---

## 4. Repository Structure

```
village-grievance-system/
├── .github/
│   └── workflows/
│       └── rag-ci.yml                 # Automated CI/CD workflow
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # Environment and system settings
│   │   ├── api/                       # REST route handlers
│   │   │   ├── ai.py                  # AI query, history, and source endpoints
│   │   │   ├── complaints.py          # Grievance CRUD and tracking
│   │   │   ├── documents.py           # Document upload, dedup, delete, reindex
│   │   │   └── auth.py                # JWT authentication and user management
│   │   ├── database/                  # Database session and schema initialization
│   │   ├── models/                    # SQLAlchemy database models
│   │   ├── schemas/                   # Pydantic input/output schemas
│   │   ├── services/                  # Core services
│   │   │   ├── document_parser.py     # Token-based chunking & SHA-256 hashing
│   │   │   ├── embedding_service.py   # Vector embedding generator
│   │   │   ├── qdrant_service.py      # Qdrant client, filter search & chunk deletion
│   │   │   ├── hybrid_retriever.py    # Hybrid SQL + Vector retrieval
│   │   │   └── llm_service.py         # LLM answer synthesis
│   │   ├── verification/              # Claim Verification Engine (CVE)
│   │   │   ├── schemas.py             # ClaimType, VerificationStatus & report contracts
│   │   │   ├── extraction/
│   │   │   │   ├── sentence_splitter.py # spaCy + administrative SBD
│   │   │   │   └── claim_extractor.py   # Atomic claim deconstructor & classifier
│   │   │   ├── evidence/
│   │   │   │   ├── db_verifier.py       # Deterministic PostgreSQL complaint/admin checker
│   │   │   │   └── evidence_mapper.py   # Multi-factor evidence-to-claim alignment
│   │   │   ├── models/
│   │   │   │   ├── model_loader.py      # Singleton NLI model loader & device detector
│   │   │   │   └── nli_classifier.py    # DeBERTa-v3 cross-encoder inference engine
│   │   │   ├── engine/                # Master Decision Engine & Scorer
│   │   │   │   ├── confidence_scorer.py # Multi-source empirical composite confidence calculator
│   │   │   │   ├── decision_engine.py   # Multi-stage claim-level verification coordinator
│   │   │   │   └── corrector.py         # Negative-constraint bounded 2-retry correction loop
│   │   │   ├── correction/            # Feature 5: Production Answer Correction Engine
│   │   │   │   ├── prompt_builder.py    # Negative-constraint prompt generator
│   │   │   │   ├── correction_controller.py # Bounded 2-retry state machine coordinator
│   │   │   │   └── audit_logger.py      # Database audit trail persister
│   │   │   └── evaluation/            # Academic evaluation datasets & metrics
│   │   ├── hallucination/             # Core decision engine & confidence scoring
│   │   └── evaluation/
│   │       ├── rag_eval_dataset.py    # 16-query RAG benchmark dataset
│   │       └── evaluator.py           # Multi-configuration comparative evaluator
│   ├── tests/
│   │   ├── run_tests.py               # End-to-end integration and regression suite
│   │   └── verification/
│   │       ├── test_extraction.py     # Claim extraction & SBD unit tests (8 tests)
│   │       ├── test_evidence.py       # DB verifier & evidence mapper unit tests (7 tests)
│   │       ├── test_nli.py            # DeBERTa NLI inference & loader unit tests (5 tests)
│   │       ├── test_confidence.py     # Confidence scorer & decision engine (8 tests)
│   │       └── test_correction.py     # Correction prompt builder, controller & audit (7 tests)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                # Reusable UI widgets, badges, evidence modals
│   │   ├── pages/                     # Citizen portal, Panchayat, Knowledge Base, Research
│   │   └── services/                  # Axios API clients
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 5. Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker for containerized execution

### Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
- On startup, the system initializes database tables and seeds demo departments, complaints, and vectorized guidelines.
- Interactive OpenAPI documentation is available at: `http://localhost:8000/docs`.

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Web portal opens at: `http://localhost:5173`.

---

## 6. Running the Test Suites

### All Verification Engine Unit Tests (35 tests)
```bash
cd backend
python -m unittest discover -s tests/verification -p "test_*.py" -v
```
Runs:
- `test_extraction.py`: 8 tests covering schema validation, SBD, abbreviation protection, and atomic proposition decomposition.
- `test_evidence.py`: 7 tests covering deterministic DB checks, department synonym resolution, non-existent complaint detection, and evidence mapping.
- `test_nli.py`: 5 tests covering singleton model loading, entailment, contradiction, neutral / insufficient evidence, and batching.
- `test_confidence.py`: 8 tests covering empirical composite confidence scoring, contradiction penalization, holistic confidence aggregation, and decision routing (`SHOW`, `CORRECT`, `ABSTAIN`).
- `test_correction.py`: 7 tests covering negative-constraint prompt generation, deterministic fallback generation, immediate acceptance of valid answers, loop correction of contradicted departments/statuses, safe abstention, and database audit trail persistence.

### End-to-End Pipeline Regression Tests
```bash
cd backend
python tests/run_tests.py
```

### RAG Evaluation Benchmark
```bash
cd backend
python app/evaluation/rag_eval_dataset.py
```

### Frontend Type-Check & Production Build
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 7. Demo Accounts (Default Password: `Password123!`)

| Role | Email | Name | Permissions |
|---|---|---|---|
| **Citizen** | `citizen@village.gov.in` | Rajesh Kumar | File grievances, track status, query AI assistant |
| **Panchayat Staff** | `staff@village.gov.in` | Anjali Sharma | Manage grievances, upload knowledge docs, re-index |
| **Dept Official** | `official@water.gov.in` | Vikram Singh | Handle department-specific complaints |
| **Admin** | `admin@village.gov.in` | Administrator | System-wide administrative controls |
| **Researcher** | `researcher@village.gov.in` | Dr. Sunita Sharma | Inspect hallucination metrics and comparative benchmarks |

---

## 8. Research Evaluation Metrics

The system tracks academic verification metrics across three evaluation configurations (**Baseline LLM**, **RAG**, and **RAG + CVE Verification**):

$$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}, \quad F_{1,c} = 2 \cdot \frac{P_c \cdot R_c}{P_c + R_c}$$

- **False Acceptance Rate (FAR)**: Proportion of contradicted or ungrounded assertions incorrectly accepted (Target $< 5\%$).
- **False Rejection Rate (FRR)**: Proportion of true, supported assertions incorrectly rejected.
- **Expected Calibration Error (ECE)**: Difference between predicted confidence and empirical accuracy across probability bins.
- **Verification Latency**: Measured processing time (ms) broken down across extraction, retrieval, DB verification, and NLI inference.

---

## 9. CI/CD Pipeline

Automated on every push and pull request via GitHub Actions:
- **Linting**: Ruff code formatting and syntax checks.
- **Unit Testing**: Pytest execution across Python 3.11 and 3.12.
- **Frontend Verification**: ESLint checks, TypeScript type-checking, and Vite production bundle build.
- **Docker Validation**: Automated container image build test.

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

### Feature 2: Claim Verification Engine (CVE) — Hallucination Detection
- **Atomic Claim Extraction**: Uses `spaCy` and rule-based linguistic decomposition to break compound answers into atomic, independently testable propositions across coordinate conjunctions (*"and"*, *";"*).
- **Indian Administrative SBD**: Sentence Boundary Detection protects honorifics (*Shri*, *Smt*, *Dr*), abbreviations (*Sec.*, *Dept.*, *No.*, *Rs.*), single-letter initials (*R. K. Sharma*), and decimal numerals (*3.5 days*, *Rs. 500.50*).
- **Hybrid Verification Pipeline**:
  - **Deterministic DB Verification**: Authoritative SQL queries verify exact attributes (Complaint ID, status, handling department, dates).
  - **NLI Cross-Encoder Verification**: DeBERTa-v3 MNLI classifies unstructured policy claims against retrieved text into `SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`.
- **Two-Retry Correction Loop**: Detects contradictions, creates targeted negative-constraint correction prompts, and triggers constrained regeneration.
- **Controlled Abstention**: Automatically refrains from answering when evidence is missing or confidence is insufficient.

---

## 3. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, Lucide Icons | Citizen grievance portal, Panchayat officer dashboard, Research verification visualizer |
| **Backend API** | Python, FastAPI, Pydantic v2, SQLAlchemy | High-performance asynchronous REST API with strict request/response validation |
| **Relational Database** | PostgreSQL (with automatic SQLite fallback) | Authoritative complaint records, users, village administrative data, verification audit logs |
| **Vector Database** | Qdrant (`qdrant-client`) | Vector storage with cosine similarity search for government documents |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`, 384d) | Dense semantic vector representations |
| **NLI Model** | Hugging Face Transformers (`DeBERTa-v3 MNLI`) | Natural Language Inference for claim-evidence verification |
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
│   │   │   ├── evidence/              # Evidence alignment & deterministic DB verifier
│   │   │   ├── models/                # DeBERTa NLI cross-encoder model wrapper
│   │   │   ├── engine/                # Decision engine, correction loop, abstention
│   │   │   └── evaluation/            # Evaluation benchmarks and metrics
│   │   ├── hallucination/             # Core decision engine & confidence scoring
│   │   └── evaluation/
│   │       ├── rag_eval_dataset.py    # 16-query RAG benchmark dataset
│   │       └── evaluator.py           # Multi-configuration comparative evaluator
│   ├── tests/
│   │   ├── run_tests.py               # End-to-end integration and regression suite
│   │   └── verification/
│   │       └── test_extraction.py     # Claim extraction & SBD unit tests
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

### Verification & Extraction Unit Tests
```bash
cd backend
python -m unittest tests/verification/test_extraction.py -v
```

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
- **Verification Latency**: Measured processing time (ms) broken down across extraction, retrieval, DB verification, and NLI inference.

---

## 9. CI/CD Pipeline

Automated on every push and pull request via GitHub Actions:
- **Linting**: Ruff code formatting and syntax checks.
- **Unit Testing**: Pytest execution across Python 3.11 and 3.12.
- **Frontend Verification**: ESLint checks, TypeScript type-checking, and Vite production bundle build.
- **Docker Validation**: Automated container image build test.

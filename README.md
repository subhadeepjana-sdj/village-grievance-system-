# Evidence-Grounded AI Village Grievance Redressal System

Production-style academic/research web application providing evidence-grounded AI question answering, grievance management, hybrid RAG retrieval, hallucination detection, and response decision control for rural Gram Panchayat governance.

---

## 1. Research Pipeline Architecture

```text
                     CITIZEN QUESTION
                            │
                            ▼
                    Hybrid Retrieval
               ┌────────────┴────────────┐
               ▼                         ▼
      PostgreSQL Record           Qdrant Vector DB
      (Complaint Facts)          (Knowledge Base)
               └────────────┬────────────┘
                            ▼
                   LLM Generation
                            │
                            ▼
                    Claim Extraction
                            │
                            ▼
                   NLI Claim Verification
               ┌────────────┼────────────┐
               ▼            ▼            ▼
           SUPPORTED   CONTRADICTED INSUFFICIENT
               │            │            │
               ▼            ▼            ▼
             SHOW       CORRECT/      ABSTAIN
                       REGENERATE
```

---

## 2. Technology Stack

- **Frontend**: React.js, Vite, Tailwind CSS, React Router, Axios, Recharts, Lucide React icons.
- **Backend**: Python FastAPI, SQLAlchemy ORM, Pydantic, JWT authentication, Argon2/bcrypt.
- **Structured DB**: PostgreSQL (with automatic SQLite fallback for standalone local execution).
- **Vector DB**: Qdrant (`qdrant-client` with local/in-memory vector storage).
- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384 dimensions).
- **LLM Service**: Configurable Gemini API via `google-genai` SDK with evidence-bound fallback engine.

---

## 3. Quick Start & Execution Instructions

### Backend Setup

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The database auto-creates and seeds default demo data, departments, complaints, and vectorized knowledge base documents on startup!

API Documentation will be available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The web application will open at `http://localhost:5173`.

---

## 4. Default Demo Accounts (Password: `Password123!`)

| Role | Email | Name |
|---|---|---|
| **Citizen** | `citizen@village.gov.in` | Rajesh Kumar |
| **Panchayat Staff** | `staff@village.gov.in` | Panchayat Staff Anjali |
| **Dept Official** | `official@water.gov.in` | Water Dept Officer Vikram |
| **Admin** | `admin@village.gov.in` | System Administrator |
| **Researcher** | `researcher@village.gov.in` | Dr. Sunita Sharma |

---

## 5. Verification & Acceptance Test Scenario

Ask the AI Assistant:
> *"Who is handling my complaint GRV-2026-001024?"*

**System Execution Trace**:
1. Extracted Complaint ID: `GRV-2026-001024`
2. Retrieved PostgreSQL Record: Status `UNDER_REVIEW`, Dept `Village Water Department`
3. Retrieved Qdrant Evidence Chunks: Water Supply Charter 2026 SLA rules
4. NLI Claim Verification: 96% Faithfulness Entailment (`SUPPORTED`)
5. Output: *"Your complaint GRV-2026-001024 is currently under review by the Village Water Department."* with `✓ Evidence Verified` badge.

If unsupported questions are asked (e.g., *"When will a space rocket launch station be built?"*), the system outputs:
> *"ABSTAIN: I could not find sufficient verified information to answer this question."*

---

## 6. Docker Deployment

```bash
docker-compose up --build
```

import sys
import os
# pyrefly: ignore [missing-import]
import pytest

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.rag.pipeline import rag_pipeline
from app.hallucination.validator import hallucination_validator
from app.hallucination.contradiction_detector import contradiction_detector

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    seed_database()
    db = SessionLocal()
    yield db
    db.close()

def test_structured_complaint_query(setup_db):
    db = setup_db
    res = rag_pipeline.run_pipeline("Who is handling my complaint GRV-2026-001024?", db, configuration="rag_verification")
    
    assert res["decision"] in ["SHOW", "SUPPORTED"]
    assert "Water Department" in res["answer"] or "Water" in res["answer"]
    assert res["verification_status"] == "SUPPORTED"
    assert res["confidence"] > 50.0

def test_contradiction_detection():
    claim = "Your complaint GRV-2026-001024 is handled by the Road Department."
    evidence_text = "COMPLAINT RECORD GRV-2026-001024: Department Handling: Village Water Department\nStatus: Under Review"
    
    res = contradiction_detector.verify_claim(claim, evidence_text)
    assert res["result"] == "CONTRADICTED"
    assert res["confidence"] > 0.8

def test_abstention_on_unsupported_query(setup_db):
    db = setup_db
    res = rag_pipeline.run_pipeline("When will the government construct a space rocket launch station in Chandanpur village?", db, configuration="rag_verification")
    
    assert res["decision"] in ["ABSTAIN", "INSUFFICIENT_EVIDENCE"] or "could not find" in res["answer"].lower()

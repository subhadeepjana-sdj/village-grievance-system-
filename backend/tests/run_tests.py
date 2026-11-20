import sys
import os

user_site = os.path.expanduser(r"~\AppData\Roaming\Python\Python314\site-packages")
if os.path.exists(user_site) and user_site not in sys.path:
    sys.path.insert(0, user_site)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from app.database.session import SessionLocal, engine, Base
from app.database.seed_data import seed_database
from app.rag.pipeline import rag_pipeline
from app.hallucination.contradiction_detector import contradiction_detector

class TestAIPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        seed_database()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_structured_complaint_query(self):
        res = rag_pipeline.run_pipeline("Who is handling my complaint GRV-2026-001024?", self.db, configuration="rag_verification")
        self.assertIn(res["decision"], ["SHOW", "SUPPORTED"])
        self.assertTrue("Water" in res["answer"] or "Water Department" in res["answer"])
        self.assertEqual(res["verification_status"], "SUPPORTED")
        self.assertGreater(res["confidence"], 50.0)
        print("[OK] Structured complaint retrieval & NLI verification test PASSED")

    def test_contradiction_detection(self):
        claim = "Your complaint GRV-2026-001024 is handled by the Road Department."
        evidence_text = "COMPLAINT RECORD GRV-2026-001024: Department Handling: Village Water Department\nStatus: Under Review"
        res = contradiction_detector.verify_claim(claim, evidence_text)
        self.assertEqual(res["result"], "CONTRADICTED")
        self.assertGreater(res["confidence"], 0.8)
        print("[OK] Contradiction detection test PASSED")

    def test_abstention_on_unsupported_query(self):
        res = rag_pipeline.run_pipeline("When will the government construct a space rocket launch station in Chandanpur village?", self.db, configuration="rag_verification")
        self.assertIn(res["decision"], ["ABSTAIN", "INSUFFICIENT_EVIDENCE"])
        self.assertTrue("could not find" in res["answer"].lower() or "insufficient" in res["answer"].lower())
        print("[OK] Abstention test PASSED")

if __name__ == '__main__':
    unittest.main()

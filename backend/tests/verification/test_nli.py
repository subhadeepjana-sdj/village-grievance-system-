import os
import sys
import unittest

# Fast offline test execution without remote HF latency
os.environ["OFFLINE_MODE"] = "1"

# Ensure app is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.verification.schemas import VerificationStatus
from app.verification.models.model_loader import nli_model_loader
from app.verification.models.nli_classifier import nli_classifier


class TestNLIInferenceEngine(unittest.TestCase):
    """Unit tests for Natural Language Inference model loader and cross-encoder classification."""

    def test_model_loader_singleton(self):
        loader1 = nli_model_loader
        from app.verification.models.model_loader import NLIModelLoader
        loader2 = NLIModelLoader()
        self.assertIs(loader1, loader2)
        self.assertIn(loader1.device, ["cpu", "cuda", "mps"])

    def test_nli_entailment_prediction(self):
        premise = "Under Gram Panchayat Water Rules 2026, water connection charges for BPL households are 100% subsidized."
        hypothesis = "BPL households receive subsidized water connection charges."

        res = nli_classifier.predict(premise, hypothesis)
        self.assertEqual(res["classification"], VerificationStatus.SUPPORTED)
        probs = res["probabilities"]
        self.assertGreaterEqual(probs["entailment"], 0.60)
        self.assertLess(probs["contradiction"], 0.20)
        self.assertAlmostEqual(probs["entailment"] + probs["contradiction"] + probs["neutral"], 1.0, places=2)

    def test_nli_contradiction_prediction(self):
        premise = "Grievance record confirms that complaint V1024 is being handled by the Village Water Department."
        hypothesis = "Complaint V1024 is assigned to the Public Works Department."

        res = nli_classifier.predict(premise, hypothesis)
        self.assertEqual(res["classification"], VerificationStatus.CONTRADICTED)
        probs = res["probabilities"]
        self.assertGreaterEqual(probs["contradiction"], 0.65)
        self.assertIn("contradiction", res["reason"].lower())

    def test_nli_neutral_insufficient_evidence(self):
        premise = "Complaint V1024 has status Under Review. Officials visited the village site."
        hypothesis = "The complaint will be resolved within 48 hours."

        res = nli_classifier.predict(premise, hypothesis)
        self.assertEqual(res["classification"], VerificationStatus.INSUFFICIENT_EVIDENCE)
        probs = res["probabilities"]
        self.assertGreaterEqual(probs["neutral"], 0.60)
        self.assertIn("insufficient", res["reason"].lower())

    def test_nli_batched_predictions(self):
        pairs = [
            ("Water pipeline repaired.", "Water pipeline is fixed."),
            ("Road repair in progress.", "Road repair was rejected."),
            ("Sanitation staff cleaned drain.", "Panchayat will build hospital in 2 years.")
        ]
        results = nli_classifier.predict_batch(pairs)
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0]["classification"], VerificationStatus.SUPPORTED)
        self.assertEqual(results[1]["classification"], VerificationStatus.CONTRADICTED)
        self.assertEqual(results[2]["classification"], VerificationStatus.INSUFFICIENT_EVIDENCE)

        for r in results:
            probs = r["probabilities"]
            self.assertAlmostEqual(probs["entailment"] + probs["contradiction"] + probs["neutral"], 1.0, places=2)


if __name__ == "__main__":
    unittest.main()

import logging
from typing import List, Dict, Any, Optional
from app.verification.schemas import (
    ClaimVerificationResult,
    VerificationStatus,
    VerificationMode,
)

logger = logging.getLogger("uvicorn.error")

class ConfidenceScorer:
    """
    Computes calibrated, multi-factor grounded confidence scores.
    Combines Source Authority, Retrieval Match Score, and NLI Probabilities.
    """

    SOURCE_AUTHORITY = {
        "COMPLAINT_RECORD": 1.0,      # Direct authoritative SQL table
        "KNOWLEDGE_BASE": 0.95,       # Verified government guidelines PDF
        "OFFICIAL_PORTAL": 0.90,      # Government circular
        "CITIZEN_SUBMISSION": 0.70,   # Citizen complaint description
        "EXTERNAL": 0.50              # Web / third-party source
    }

    CONTRADICTION_PENALTY_LAMBDA = 2.0

    def calculate_claim_confidence(
        self,
        source_type: str,
        match_score: float,
        p_entailment: float,
        p_contradiction: float,
        verification_mode: VerificationMode = VerificationMode.NLI_MODEL
    ) -> float:
        """
        Calculates calibrated confidence score (0.0 to 1.0) for a single claim.
        Formula: C = A_source * S_match * max(0, p_E - lambda * p_C)
        """
        # Deterministic DB checks already have exact binary confidence
        if verification_mode == VerificationMode.DETERMINISTIC_DB:
            return 1.0 if p_entailment >= 0.9 else 0.0

        authority = self.SOURCE_AUTHORITY.get(source_type.upper(), 0.70)
        relevance = max(0.1, min(match_score, 1.0))

        # Contradiction-penalized entailment margin
        margin = max(0.0, p_entailment - (self.CONTRADICTION_PENALTY_LAMBDA * p_contradiction))

        calibrated_score = authority * relevance * margin
        return round(min(max(calibrated_score, 0.0), 1.0), 4)

    def calculate_overall_confidence(
        self,
        claims: List[ClaimVerificationResult]
    ) -> float:
        """
        Calculates aggregate response-level confidence score (0.0 to 100.0%).
        Severely penalizes contradictions to prevent false-acceptance of hallucinations.
        """
        if not claims:
            return 0.0

        total = len(claims)
        contradicted_count = sum(1 for c in claims if c.status == VerificationStatus.CONTRADICTED)
        supported_count = sum(1 for c in claims if c.status == VerificationStatus.SUPPORTED)

        # Severe penalty if any claim is refuted by authoritative facts
        if contradicted_count > 0:
            penalty = contradicted_count * 20.0
            return round(max(0.0, 35.0 - penalty), 1)

        # Coverage ratio: fraction of claims grounded in verified evidence
        support_ratio = supported_count / total

        # Average confidence of the supported subset
        supported_confidences = [c.confidence for c in claims if c.status == VerificationStatus.SUPPORTED]
        avg_supported_conf = sum(supported_confidences) / len(supported_confidences) if supported_confidences else 0.0

        # Weighted combination: 70% coverage weight + 30% individual claim confidence
        overall = (support_ratio * 0.70 + avg_supported_conf * 0.30) * 100.0
        return round(min(max(overall, 0.0), 99.0), 1)


confidence_scorer = ConfidenceScorer()

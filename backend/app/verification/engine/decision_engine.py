import time
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.verification.schemas import (
    AtomicClaim,
    EvidenceItem,
    ClaimType,
    VerificationStatus,
    VerificationMode,
    ClaimVerificationResult,
    VerificationReport,
)
from app.verification.extraction.claim_extractor import atomic_claim_extractor
from app.verification.evidence.db_verifier import db_verifier
from app.verification.evidence.evidence_mapper import evidence_mapper
from app.verification.models.nli_classifier import nli_classifier
from app.verification.engine.confidence_scorer import confidence_scorer

logger = logging.getLogger("uvicorn.error")

class DecisionEngine:
    """
    Master Decision Engine for Claim-Level Verification.
    Coordinates Claim Extraction -> DB Checks -> Evidence Mapping -> NLI Inference -> Confidence Aggregation.
    """

    def verify_answer(
        self,
        answer: str,
        evidence_pool: List[Any],
        db: Optional[Session] = None,
        use_llm_extractor: bool = False
    ) -> VerificationReport:
        """
        Runs complete claim-level verification over an AI-generated answer.
        """
        start_time = time.time()
        verification_id = f"VER-{uuid.uuid4().hex[:8].upper()}"

        if not answer or not answer.strip():
            return VerificationReport(
                verification_id=verification_id,
                original_answer="",
                overall_status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                action_taken="ABSTAIN",
                overall_confidence=0.0,
                claims=[],
                total_claims=0,
                execution_time_ms=0.0
            )

        # 1. Atomic Claim Extraction
        extracted_claims: List[AtomicClaim] = atomic_claim_extractor.extract_atomic_claims(
            answer, use_llm=use_llm_extractor
        )

        claim_results: List[ClaimVerificationResult] = []

        # 2. Dual-Track Verification for Each Claim
        for claim in extracted_claims:
            # Track A: Deterministic Database Verifier
            if db is not None and db_verifier.can_verify(claim):
                db_res = db_verifier.verify_claim(claim, db)
                if db_res is not None:
                    claim_results.append(db_res)
                    continue

            # Track B: Evidence Mapping + NLI Cross-Encoder
            match = evidence_mapper.find_best_evidence(claim, evidence_pool)
            if not match.evidence_item:
                # No evidence passage found for this claim
                claim_results.append(
                    ClaimVerificationResult(
                        claim=claim,
                        status=VerificationStatus.INSUFFICIENT_EVIDENCE,
                        confidence=0.0,
                        verification_mode=VerificationMode.FALLBACK,
                        matched_evidence_id=None,
                        matched_evidence_text=None,
                        probabilities={"entailment": 0.05, "contradiction": 0.05, "neutral": 0.90},
                        reason="No relevant evidence chunk available in verified records."
                    )
                )
                continue

            # NLI Forward Pass
            nli_pred = nli_classifier.predict(match.premise_text, claim.claim_text)
            probs = nli_pred["probabilities"]

            # Composite Calibrated Confidence Calculation
            calibrated_conf = confidence_scorer.calculate_claim_confidence(
                source_type=match.evidence_item.source_type,
                match_score=match.match_score,
                p_entailment=probs["entailment"],
                p_contradiction=probs["contradiction"],
                verification_mode=VerificationMode.NLI_MODEL
            )

            claim_results.append(
                ClaimVerificationResult(
                    claim=claim,
                    status=nli_pred["classification"],
                    confidence=calibrated_conf,
                    verification_mode=VerificationMode.NLI_MODEL,
                    matched_evidence_id=match.source_id,
                    matched_evidence_text=match.evidence_item.evidence_text[:300],
                    probabilities=probs,
                    reason=nli_pred["reason"]
                )
            )

        # 3. Aggregate Outcomes
        total = len(claim_results)
        supported_count = sum(1 for c in claim_results if c.status == VerificationStatus.SUPPORTED)
        contradicted_count = sum(1 for c in claim_results if c.status == VerificationStatus.CONTRADICTED)
        insufficient_count = sum(1 for c in claim_results if c.status == VerificationStatus.INSUFFICIENT_EVIDENCE)

        overall_conf = confidence_scorer.calculate_overall_confidence(claim_results)

        # 4. Final Verdict & Action Policy
        if contradicted_count > 0:
            overall_status = VerificationStatus.CONTRADICTED
            action_taken = "CORRECT"
            directive = self._build_correction_directive(claim_results)
        elif supported_count > 0 and supported_count >= insufficient_count and overall_conf >= 55.0:
            overall_status = VerificationStatus.SUPPORTED
            action_taken = "SHOW"
            directive = None
        else:
            overall_status = VerificationStatus.INSUFFICIENT_EVIDENCE
            action_taken = "ABSTAIN"
            directive = None

        elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

        return VerificationReport(
            verification_id=verification_id,
            original_answer=answer,
            overall_status=overall_status,
            action_taken=action_taken,
            overall_confidence=overall_conf,
            claims=claim_results,
            total_claims=total,
            supported_claims=supported_count,
            contradicted_claims=contradicted_count,
            insufficient_claims=insufficient_count,
            correction_directive=directive,
            execution_time_ms=elapsed_ms
        )

    def _build_correction_directive(self, claims: List[ClaimVerificationResult]) -> str:
        """Constructs targeted negative-constraint instructions for the correction engine."""
        contradictions = [c for c in claims if c.status == VerificationStatus.CONTRADICTED]
        directives = []
        for c in contradictions:
            directives.append(
                f"- Claim '{c.claim.claim_text}' is refuted by official records ({c.reason}). "
                f"Ground fact: {c.matched_evidence_text or 'Refer to verified records.'}"
            )
        return "CORRECTION INSTRUCTIONS:\n" + "\n".join(directives)


decision_engine = DecisionEngine()

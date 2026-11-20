import logging
from typing import List, Dict, Any, Optional
from app.verification.schemas import VerificationReport, VerificationStatus, ClaimVerificationResult

logger = logging.getLogger("uvicorn.error")

class CorrectionPromptBuilder:
    """
    Constructs high-precision correction prompts with explicit negative constraints
    and anchored evidence context to prevent hallucination cycles during regeneration.
    """

    SYSTEM_DIRECTIVE = (
        "You are the official Evidence-Grounded Verification Assistant for Gram Panchayat Redressal.\n"
        "Your previous candidate answer contained factual contradictions or unverified assertions.\n"
        "You must regenerate the response strictly following the negative constraints and verified records below."
    )

    def build_correction_prompt(
        self,
        question: str,
        candidate_answer: str,
        report: VerificationReport,
        evidence_pool: List[Any],
        attempt: int = 1
    ) -> str:
        """
        Builds a structured correction prompt containing:
          1. Original citizen question.
          2. Explicitly refuted claims and ground truth facts.
          3. Unsupported claims that must be omitted or qualified.
          4. Strict negative constraints (e.g., 'Do NOT claim...').
          5. Preserved evidence items.
        """
        contradictions = [c for c in report.claims if c.status == VerificationStatus.CONTRADICTED]
        unsupported = [c for c in report.claims if c.status == VerificationStatus.INSUFFICIENT_EVIDENCE]

        # 1. Format Refuted Claims
        refuted_section = []
        for i, c in enumerate(contradictions, 1):
            refuted_section.append(
                f"  [{i}] REFUTED CLAIM: \"{c.claim.claim_text}\"\n"
                f"      ERROR REASON: {c.reason}\n"
                f"      VERIFIED GROUND TRUTH: {c.matched_evidence_text or 'Refer to official records.'}"
            )
        refuted_text = "\n".join(refuted_section) if refuted_section else "  None"

        # 2. Format Unsupported Claims
        unsupported_section = []
        for i, c in enumerate(unsupported, 1):
            unsupported_section.append(
                f"  [{i}] UNVERIFIED CLAIM: \"{c.claim.claim_text}\" (No official record found)"
            )
        unsupported_text = "\n".join(unsupported_section) if unsupported_section else "  None"

        # 3. Format Negative Constraints
        negative_rules = [
            "- Do NOT repeat any of the refuted claims listed above.",
            "- Do NOT invent, assume, or extrapolate resolution dates, deadlines, or officer names.",
            "- If a detail (such as resolution timeframe) is not in the verified evidence, explicitly state that it is not yet confirmed in village records.",
            "- Use ONLY the verified facts provided in the evidence context.",
            "- Keep the tone polite, clear, and direct for rural citizens."
        ]
        negative_rules_text = "\n".join(negative_rules)

        # 4. Format Evidence Pool Context
        evidence_lines = []
        for i, item in enumerate(evidence_pool, 1):
            source_type = item.get("source_type", "RECORD") if isinstance(item, dict) else getattr(item, "source_type", "RECORD")
            text = item.get("evidence_text") or item.get("text") if isinstance(item, dict) else getattr(item, "evidence_text", "")
            evidence_lines.append(f"--- VERIFIED EVIDENCE [{i}] ({source_type}) ---\n{text.strip()}")
        evidence_context = "\n\n".join(evidence_lines)

        prompt = (
            f"{self.SYSTEM_DIRECTIVE}\n\n"
            f"[CORRECTION ROUND #{attempt}]\n"
            f"CITIZEN QUESTION:\n{question}\n\n"
            f"PREVIOUS CANDIDATE ANSWER (REJECTED):\n\"{candidate_answer}\"\n\n"
            f"FACTUAL CONTRADICTIONS DETECTED:\n{refuted_text}\n\n"
            f"UNSUPPORTED / UNVERIFIED CLAIMS:\n{unsupported_text}\n\n"
            f"NEGATIVE CONSTRAINTS (MANDATORY TO FOLLOW):\n{negative_rules_text}\n\n"
            f"OFFICIAL VERIFIED EVIDENCE CONTEXT:\n{evidence_context}\n\n"
            f"Now regenerate a concise, 100% factually accurate answer grounded exclusively in the evidence above:"
        )

        return prompt

    def build_deterministic_fallback(
        self,
        report: VerificationReport,
        evidence_pool: List[Any]
    ) -> str:
        """
        Constructs an unembellished factual statement directly from verified evidence items
        when all regeneration attempts fail to pass verification.
        """
        # 1. Check if structured complaint records exist
        for item in evidence_pool:
            source_type = item.get("source_type") if isinstance(item, dict) else getattr(item, "source_type", None)
            if source_type == "COMPLAINT_RECORD":
                text = item.get("evidence_text", "") if isinstance(item, dict) else getattr(item, "evidence_text", "")
                if text:
                    return f"Verified Record: {text.strip()}"

        # 2. Check knowledge base passages
        for item in evidence_pool:
            text = item.get("evidence_text") or item.get("text") if isinstance(item, dict) else getattr(item, "evidence_text", "")
            if text:
                return f"Official Village Record: {text[:250].strip()}..."

        return "I could not find sufficient verified information in village records to answer this question. Please contact the Gram Panchayat office."


correction_prompt_builder = CorrectionPromptBuilder()

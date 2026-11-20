"""
Claim Verification Engine (CVE) Package
An evidence-grounded verification subsystem for atomic claim-level hallucination detection.
"""

from app.verification.schemas import (
    ClaimType,
    VerificationStatus,
    VerificationMode,
    AtomicClaim,
    EvidenceItem,
    ClaimVerificationResult,
    VerificationReport,
)

__all__ = [
    "ClaimType",
    "VerificationStatus",
    "VerificationMode",
    "AtomicClaim",
    "EvidenceItem",
    "ClaimVerificationResult",
    "VerificationReport",
]

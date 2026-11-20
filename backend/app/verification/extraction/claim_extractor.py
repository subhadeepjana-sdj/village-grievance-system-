import re
import json
import logging
from typing import List, Dict, Any, Optional
from app.verification.schemas import AtomicClaim, ClaimType
from app.verification.extraction.sentence_splitter import sentence_splitter
from app.config import settings

logger = logging.getLogger("uvicorn.error")

class AtomicClaimExtractor:
    """
    Deconstructs generated answers into atomic, independent factual propositions.
    Combines rule-based linguistic decomposition with structured LLM extraction.
    """

    COMPLAINT_PATTERN = re.compile(r'\b(GRV-\d{4}-\d+|\bV\d{3,6}\b|\bGRV\d+\b)', re.IGNORECASE)
    TIMELINE_PATTERN = re.compile(r'(\d+)\s*(days?|weeks?|months?|hours?|working days?)', re.IGNORECASE)

    KNOWN_DEPARTMENTS = [
        "Village Water Department", "Water Department", "Water Supply",
        "Roads & Infrastructure", "Roads Department", "Road Department", "Public Works Department", "PWD",
        "Sanitation & Waste Management", "Sanitation Department",
        "Electricity & Power", "Electricity Department",
        "Public Health & Schemes", "Health Department", "Health & Family Welfare",
        "Education Department", "Revenue Department", "Panchayat Administration"
    ]

    KNOWN_STATUSES = [
        "SUBMITTED", "ACKNOWLEDGED", "ASSIGNED", "UNDER_REVIEW", "IN_PROGRESS",
        "RESOLVED", "REJECTED", "CLOSED", "Under Review", "In Progress", "Resolved"
    ]

    def extract_atomic_claims(
        self,
        answer: str,
        use_llm: bool = True
    ) -> List[AtomicClaim]:
        """
        Extracts a list of typed AtomicClaim objects from raw response text.
        """
        if not answer or not answer.strip():
            return []

        # 1. If LLM is enabled and configured, attempt structured extraction
        if use_llm and getattr(settings, "LLM_API_KEY", None) and settings.LLM_API_KEY != "ci-dummy-key":
            try:
                llm_claims = self._extract_with_llm(answer)
                if llm_claims:
                    return llm_claims
            except Exception as e:
                logger.warning(f"LLM claim extraction failed ({e}). Falling back to rule-based engine.")

        # 2. Resilient Rule-Based Decomposition Engine
        return self._rule_based_extract(answer)

    def _rule_based_extract(self, text: str) -> List[AtomicClaim]:
        """
        High-precision rule-based atomic proposition extractor.
        Splits on sentence boundaries, then decomposes compound clauses.
        """
        sentences = sentence_splitter.split_sentences(text)
        claims: List[AtomicClaim] = []
        claim_counter = 1

        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            # Skip meta-phrases that are not factual claims
            if self._is_meta_sentence(sent_clean):
                continue

            # Decompose sentence into atomic clauses
            clauses = self._decompose_sentence_clauses(sent_clean)

            for clause in clauses:
                c_clean = clause.strip()
                if len(c_clean) < 5:
                    continue

                claim_type = self._classify_claim_type(c_clean)
                entities = self._extract_entities(c_clean)

                claims.append(
                    AtomicClaim(
                        claim_id=f"C{claim_counter}",
                        claim_text=c_clean,
                        claim_type=claim_type,
                        source_sentence=sent_clean,
                        extracted_entities=entities
                    )
                )
                claim_counter += 1

        # If everything got filtered out, keep original text as single claim
        if not claims:
            claims.append(
                AtomicClaim(
                    claim_id="C1",
                    claim_text=text.strip(),
                    claim_type=ClaimType.GENERAL_FACT,
                    source_sentence=text.strip(),
                    extracted_entities=self._extract_entities(text)
                )
            )

        return claims

    def _decompose_sentence_clauses(self, sentence: str) -> List[str]:
        """
        Breaks compound sentences into independent factual assertions.
        Handles coordinate conjunctions ("and", "but", ";", "while") when both
        parts contain subject/predicate or specific entities.
        """
        # Split on semicolon first
        parts = [p.strip() for p in sentence.split(';') if p.strip()]
        atomic_clauses = []

        for part in parts:
            # Check for patterns like "Your complaint X is assigned to Y and will be resolved in Z"
            and_splits = re.split(r'\b(?:and\s+also|and\s+is|and\s+will\s+be|and\s+has\s+been|and)\b', part, flags=re.IGNORECASE)
            
            if len(and_splits) > 1:
                # Ensure each split looks like a meaningful claim (> 15 chars)
                meaningful = True
                for s in and_splits:
                    if len(s.strip().split()) < 2:
                        meaningful = False
                        break

                if meaningful:
                    # Inherit context: if second part misses complaint ID, propagate prefix
                    complaint_match = self.COMPLAINT_PATTERN.search(and_splits[0])
                    prefix = f"For complaint {complaint_match.group(0)}, " if complaint_match else ""

                    for i, s in enumerate(and_splits):
                        sub_claim = s.strip()
                        if i > 0 and prefix and not self.COMPLAINT_PATTERN.search(sub_claim):
                            sub_claim = f"{prefix}{sub_claim}"
                        atomic_clauses.append(sub_claim)
                    continue

            atomic_clauses.append(part)

        return atomic_clauses if atomic_clauses else [sentence]

    def _classify_claim_type(self, text: str) -> ClaimType:
        """Classifies proposition into the ClaimType taxonomy."""
        text_lower = text.lower()

        # 1. Timeline
        if self.TIMELINE_PATTERN.search(text) and any(w in text_lower for w in ["resolve", "resolved", "timeline", "within", "expected", "sla", "days"]):
            return ClaimType.RESOLUTION_TIMELINE

        # 2. Complaint Identity
        if self.COMPLAINT_PATTERN.search(text) and any(w in text_lower for w in ["complaint", "number", "id", "registered", "filed"]):
            if any(w in text_lower for w in ["assigned", "handling", "department"]):
                return ClaimType.DEPARTMENT_ASSIGNMENT
            if any(s.lower() in text_lower for s in self.KNOWN_STATUSES):
                return ClaimType.STATUS
            return ClaimType.COMPLAINT_IDENTITY

        # 3. Department Assignment
        if any(dept.lower() in text_lower for dept in self.KNOWN_DEPARTMENTS) or "department" in text_lower:
            return ClaimType.DEPARTMENT_ASSIGNMENT

        # 4. Status
        if any(f"status is {s.lower()}" in text_lower or f"status: {s.lower()}" in text_lower or f"currently {s.lower()}" in text_lower for s in self.KNOWN_STATUSES):
            return ClaimType.STATUS

        # 5. Procedure Step
        if any(w in text_lower for w in ["submit", "application", "form", "office", "apply", "step", "fee", "documents required"]):
            return ClaimType.PROCEDURE_STEP

        # 6. Policy Rule
        if any(w in text_lower for w in ["scheme", "eligibility", "criteria", "guideline", "rule", "bpl", "subsidy", "act", "section"]):
            return ClaimType.POLICY_RULE

        return ClaimType.GENERAL_FACT

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extracts key entities for subsequent deterministic DB checks."""
        entities = {}
        
        # Complaint Number
        c_match = self.COMPLAINT_PATTERN.search(text)
        if c_match:
            entities["complaint_number"] = c_match.group(0).upper()

        # Department
        text_lower = text.lower()
        for dept in self.KNOWN_DEPARTMENTS:
            if dept.lower() in text_lower:
                entities["department"] = dept
                break

        # Status
        for status in self.KNOWN_STATUSES:
            if status.lower() in text_lower:
                entities["status"] = status.upper().replace(" ", "_")
                break

        # Timeline
        t_match = self.TIMELINE_PATTERN.search(text)
        if t_match:
            entities["timeline_value"] = int(t_match.group(1))
            entities["timeline_unit"] = t_match.group(2).lower()

        return entities

    def _is_meta_sentence(self, sentence: str) -> bool:
        """Filters conversational filler that carries no factual assertions."""
        lower = sentence.lower()
        fillers = [
            "hello", "hi there", "greetings", "hope this helps",
            "let me know if you need anything else", "please feel free to ask",
            "thank you for reaching out", "i am an ai assistant"
        ]
        return any(lower.startswith(f) or lower == f for f in fillers)

    def _extract_with_llm(self, text: str) -> List[AtomicClaim]:
        """Uses Gemini API with JSON structured prompt to extract atomic claims."""
        from google import genai
        client = genai.Client(api_key=settings.LLM_API_KEY)

        prompt = (
            "You are a factual claim extraction system for village governance.\n"
            "Break the following text into distinct, atomic, non-overlapping factual claims.\n"
            "Each claim must be an independent proposition that can be verified separately.\n\n"
            f"Text: \"{text}\"\n\n"
            "Return valid JSON in this exact structure:\n"
            "[\n"
            "  {\n"
            "    \"claim_text\": \"The complaint ID is GRV-2026-001024\",\n"
            "    \"claim_type\": \"complaint_identity\"\n"
            "  }\n"
            "]\n"
            "Valid claim types: complaint_identity, department_assignment, status, resolution_timeline, policy_rule, procedure_step, general_fact.\n"
            "Do NOT include conversational greetings or closing pleasantries."
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        raw_json = response.text.strip()
        data = json.loads(raw_json)

        claims = []
        for i, item in enumerate(data):
            c_text = item.get("claim_text", "").strip()
            if not c_text:
                continue

            c_type_str = item.get("claim_type", "general_fact")
            try:
                c_type = ClaimType(c_type_str)
            except ValueError:
                c_type = ClaimType.GENERAL_FACT

            claims.append(
                AtomicClaim(
                    claim_id=f"C{i+1}",
                    claim_text=c_text,
                    claim_type=c_type,
                    source_sentence=text,
                    extracted_entities=self._extract_entities(c_text)
                )
            )

        return claims


atomic_claim_extractor = AtomicClaimExtractor()

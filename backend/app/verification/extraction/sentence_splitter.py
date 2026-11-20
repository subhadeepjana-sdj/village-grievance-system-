import re
import logging
from typing import List

logger = logging.getLogger("uvicorn.error")

class SentenceSplitter:
    """
    Robust sentence boundary detector (SBD) for administrative & grievance text.
    Uses spaCy when available, with a resilient rule-based regex fallback
    that handles honorifics, abbreviations, section codes, and bullet points.
    """
    # Common abbreviations & honorifics in Indian administrative text
    PROTECTED_ABBREVIATIONS = [
        r"Mr\.", r"Mrs\.", r"Ms\.", r"Dr\.", r"Prof\.", r"Shri\.", r"Shri", r"Smt\.", r"Smt",
        r"e\.g\.", r"i\.e\.", r"etc\.", r"vs\.", r"al\.", r"approx\.",
        r"Sec\.", r"No\.", r"Dept\.", r"Govt\.", r"Panch\.", r"Ltd\.", r"Corp\.",
        r"Rs\.", r"INR"
    ]

    def __init__(self):
        self._spacy_nlp = self._init_spacy()

    def _init_spacy(self):
        """Attempts to load spaCy pipeline; returns None if not installed."""
        try:
            import spacy  # type: ignore[import-not-found]  # noqa: F401
            try:
                return spacy.load("en_core_web_sm")  # type: ignore[attr-defined]
            except Exception:
                # If model not downloaded, use blank model with sentencizer
                nlp = spacy.blank("en")  # type: ignore[attr-defined]
                nlp.add_pipe("sentencizer")
                return nlp
        except ImportError:
            logger.info("spaCy not found. Using high-precision rule-based sentence segmenter.")
            return None

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits raw generated text into grammatically sound sentences.
        """
        if not text or not text.strip():
            return []

        cleaned = text.strip()

        # 1. Try spaCy first if available
        if self._spacy_nlp is not None:
            try:
                doc = self._spacy_nlp(cleaned)
                sents = [s.text.strip() for s in doc.sents if s.text.strip()]
                if sents:
                    return sents
            except Exception as e:
                logger.warning(f"spaCy sentence splitting failed ({e}), using rule-based fallback.")

        # 2. Rule-based sentence segmentation fallback
        return self._rule_based_split(cleaned)

    def _rule_based_split(self, text: str) -> List[str]:
        # Pre-process: replace newlines with delimiters if separated by punctuation or list markers
        text = re.sub(r'\r\n|\r', '\n', text)

        # Protect abbreviations by temporarily replacing their dots
        token_map = {}
        counter = 0

        def _mask_abbrev(match):
            nonlocal counter
            key = f"__ABBR_{counter}__"
            token_map[key] = match.group(0)
            counter += 1
            return key

        masked_text = text
        for abbr in self.PROTECTED_ABBREVIATIONS:
            masked_text = re.sub(r'\b' + abbr, _mask_abbrev, masked_text, flags=re.IGNORECASE)

        # Protect single-letter initials (e.g., "R. K. Sharma", "A. P. J.")
        masked_text = re.sub(r'\b([A-Z])\.', r'__INIT_\1__', masked_text)

        # Protect floating decimals: e.g. 3.5 days, Rs. 10.50
        def _mask_decimal(match):
            nonlocal counter
            key = f"__DEC_{counter}__"
            token_map[key] = match.group(0)
            counter += 1
            return key

        masked_text = re.sub(r'\d+\.\d+', _mask_decimal, masked_text)

        # Split on sentence terminals followed by whitespace/newlines or end-of-string
        raw_splits = re.split(r'(?<=[.!?])\s+|\n{2,}|\n(?=[-*•\d]+\.?\s)', masked_text)

        sentences = []
        for s in raw_splits:
            s_clean = s.strip()
            if not s_clean:
                continue

            # Restore masked abbreviations, initials, and decimals
            for token, orig in token_map.items():
                s_clean = s_clean.replace(token, orig)
            s_clean = re.sub(r'__INIT_([A-Z])__', r'\1.', s_clean)

            # Strip leading list bullets/numbers
            s_clean = re.sub(r'^([*•\-–]|\d+[\.\)])\s*', '', s_clean).strip()

            if s_clean:
                sentences.append(s_clean)

        return sentences


sentence_splitter = SentenceSplitter()

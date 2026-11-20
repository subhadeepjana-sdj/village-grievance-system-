"""
RAG Evaluation Dataset  — Feature 1 (Knowledge Retrieval)
==========================================================

Purpose
-------
This module provides a *separate* evaluation dataset specifically for assessing
the RAG pipeline's retrieval and generation quality.

It is **different from** ``backend/app/evaluation/benchmark_questions.py``, which
tests the full end-to-end pipeline.  This dataset focuses on:

  1. Retrieval precision — does the system surface the right document/chunk?
  2. Answer faithfulness — is the generated answer grounded in the retrieved text?
  3. Abstention accuracy — does the system ABSTAIN when no evidence exists?
  4. Multi-hop — can the system combine PostgreSQL + Qdrant evidence?
  5. Department-scoped — does the department filter correctly narrow results?
  6. Validity/expiry — are outdated documents correctly excluded?

Usage
-----
    python backend/app/evaluation/rag_eval_dataset.py

The script prints a summary report to stdout.  Integrate with pytest by
importing ``RAG_EVAL_QUESTIONS`` and iterating over the cases.

Dataset schema
--------------
Each entry is a dict with:
  question          str   — the user query
  expected_sources  list  — document IDs or chunk patterns expected to appear
                            (empty list means "no KB evidence expected")
  expected_decision str   — SHOW | ABSTAIN | CORRECT
  expected_keywords list  — keywords that *must* appear in the final answer
                            (checked case-insensitively)
  forbidden_keywords list — keywords that must NOT appear (hallucination markers)
  department_filter str|None — optional department filter to pass with the query
  category          str   — retrieval / abstention / multi-hop / dept-filter / validity
  notes             str   — human-readable rationale
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

RAG_EVAL_QUESTIONS: List[Dict[str, Any]] = [

    # ------------------------------------------------------------------ #
    # Category: retrieval — standard knowledge-base lookup               #
    # ------------------------------------------------------------------ #
    {
        "question": "What documents are required to apply for a village water connection scheme?",
        "expected_sources": [],           # Populated once real docs are indexed
        "expected_decision": "SHOW",
        "expected_keywords": ["document", "apply", "water"],
        "forbidden_keywords": ["I don't know", "unable to find"],
        "department_filter": None,
        "category": "retrieval",
        "notes": "Core happy-path: KB should surface water-scheme guidelines."
    },
    {
        "question": "What is the procedure for registering a land dispute in the Panchayat?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["register", "land", "panchayat"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "retrieval",
        "notes": "Tests retrieval from revenue/land-records category."
    },
    {
        "question": "What are the eligibility criteria for the PM Awas Yojana housing scheme?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["eligibility", "housing", "scheme"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "retrieval",
        "notes": "Central government scheme — tests if indexed guidelines are retrieved."
    },
    {
        "question": "What is the timeline for resolving a road repair complaint?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["days", "resolution", "complaint"],
        "forbidden_keywords": [],
        "department_filter": "Public Works Department",
        "category": "retrieval",
        "notes": "Tests department-scoped retrieval for PWD SLA documents."
    },
    {
        "question": "What are the duties of the Gram Panchayat secretary?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["secretary", "gram panchayat", "duties"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "retrieval",
        "notes": "Administrative governance document retrieval."
    },

    # ------------------------------------------------------------------ #
    # Category: abstention — no KB evidence; expect ABSTAIN              #
    # ------------------------------------------------------------------ #
    {
        "question": "What is the boiling point of tungsten?",
        "expected_sources": [],
        "expected_decision": "ABSTAIN",
        "expected_keywords": [],
        "forbidden_keywords": ["5555", "5828"],    # hallucinated temperature values
        "department_filter": None,
        "category": "abstention",
        "notes": "Completely off-domain: should trigger ABSTAIN, not hallucinate a chemistry fact."
    },
    {
        "question": "Who won the FIFA World Cup in 2022?",
        "expected_sources": [],
        "expected_decision": "ABSTAIN",
        "expected_keywords": [],
        "forbidden_keywords": ["Argentina", "France", "Mbappe"],
        "department_filter": None,
        "category": "abstention",
        "notes": "Sports query outside village governance domain."
    },
    {
        "question": "What is the stock price of Reliance Industries today?",
        "expected_sources": [],
        "expected_decision": "ABSTAIN",
        "expected_keywords": [],
        "forbidden_keywords": ["rupees", "INR", "₹"],
        "department_filter": None,
        "category": "abstention",
        "notes": "Real-time financial data — system must not hallucinate prices."
    },

    # ------------------------------------------------------------------ #
    # Category: multi-hop — combine PostgreSQL complaint + Qdrant KB     #
    # ------------------------------------------------------------------ #
    {
        "question": "My complaint GRV-2024-001 is about a road repair. What is the standard SLA for road complaints?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["complaint", "road", "days"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "multi-hop",
        "notes": "Requires PostgreSQL hit for the complaint record AND Qdrant hit for SLA policy doc."
    },
    {
        "question": "What department handles water supply complaints and what documents do I need to submit?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["water", "department", "document"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "multi-hop",
        "notes": "Department lookup (structured) + scheme-document retrieval (semantic)."
    },

    # ------------------------------------------------------------------ #
    # Category: department filter — retrieval must respect filter param  #
    # ------------------------------------------------------------------ #
    {
        "question": "What are the sanitation guidelines for rural areas?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["sanitation", "rural"],
        "forbidden_keywords": [],
        "department_filter": "Health Department",
        "category": "dept-filter",
        "notes": "Filter: Health Department only.  Results from other depts must not appear."
    },
    {
        "question": "What are the norms for constructing a new village school?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["school", "construction", "norms"],
        "forbidden_keywords": [],
        "department_filter": "Education Department",
        "category": "dept-filter",
        "notes": "Filter: Education Department only."
    },

    # ------------------------------------------------------------------ #
    # Category: validity — outdated/unverified docs should be excluded   #
    # ------------------------------------------------------------------ #
    {
        "question": "What are the current pension scheme rates for senior citizens?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["pension", "rate"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "validity",
        "notes": (
            "Retrieval must only return chunks with status='verified'. "
            "If an older pension doc is marked 'expired' in its Qdrant payload, "
            "it must NOT appear in results."
        )
    },
    {
        "question": "What is the BPL income limit for welfare scheme eligibility?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["BPL", "income", "eligibility"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "validity",
        "notes": "Income threshold changes over years; only 'verified' status doc must be used."
    },

    # ------------------------------------------------------------------ #
    # Category: edge — empty / very short / ambiguous queries            #
    # ------------------------------------------------------------------ #
    {
        "question": "help",
        "expected_sources": [],
        "expected_decision": "ABSTAIN",
        "expected_keywords": [],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "edge",
        "notes": "Single-word ambiguous query — no context, should ABSTAIN or return a clarifying response."
    },
    {
        "question": "What is the Panchayat?",
        "expected_sources": [],
        "expected_decision": "SHOW",
        "expected_keywords": ["panchayat"],
        "forbidden_keywords": [],
        "department_filter": None,
        "category": "edge",
        "notes": "Very broad question — system should answer with general governance doc if available."
    },
]


# ------------------------------------------------------------------ #
#  Utility: run a quick offline schema validation (no server needed)  #
# ------------------------------------------------------------------ #

REQUIRED_KEYS = {
    "question", "expected_sources", "expected_decision", "expected_keywords",
    "forbidden_keywords", "department_filter", "category", "notes"
}
VALID_DECISIONS = {"SHOW", "ABSTAIN", "CORRECT"}
VALID_CATEGORIES = {"retrieval", "abstention", "multi-hop", "dept-filter", "validity", "edge"}


def validate_dataset(dataset: List[Dict[str, Any]]) -> None:
    errors: List[str] = []
    for idx, item in enumerate(dataset):
        label = f"[item {idx}] '{item.get('question', '')[:60]}'"

        missing = REQUIRED_KEYS - set(item.keys())
        if missing:
            errors.append(f"{label}: missing keys {missing}")

        if item.get("expected_decision") not in VALID_DECISIONS:
            errors.append(f"{label}: invalid expected_decision '{item.get('expected_decision')}'")

        if item.get("category") not in VALID_CATEGORIES:
            errors.append(f"{label}: invalid category '{item.get('category')}'")

    if errors:
        raise ValueError("RAG eval dataset validation failed:\n" + "\n".join(errors))

    print(f"[OK] RAG eval dataset: {len(dataset)} questions validated.")

    # Print breakdown by category
    from collections import Counter
    counts = Counter(item["category"] for item in dataset)
    print("\nCategory breakdown:")
    for cat, n in sorted(counts.items()):
        print(f"  {cat:<20} {n} question(s)")
    print(f"\nDecision breakdown:")
    dcounts = Counter(item["expected_decision"] for item in dataset)
    for dec, n in sorted(dcounts.items()):
        print(f"  {dec:<20} {n} question(s)")


if __name__ == "__main__":
    validate_dataset(RAG_EVAL_QUESTIONS)

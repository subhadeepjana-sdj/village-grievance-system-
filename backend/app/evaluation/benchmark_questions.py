BENCHMARK_DATASET = [
    {
        "id": 1,
        "question": "Who is handling my complaint GRV-2026-001024?",
        "expected_answer": "Village Water Department",
        "expected_status": "Under Review",
        "category": "Structured Complaint Lookup"
    },
    {
        "id": 2,
        "question": "What is the status of road repair complaint GRV-2026-001025?",
        "expected_answer": "In Progress",
        "expected_status": "In Progress",
        "category": "Structured Complaint Lookup"
    },
    {
        "id": 3,
        "question": "What is the official deadline for resolving drinking water supply complaints?",
        "expected_answer": "48 hours from submission",
        "expected_status": "N/A",
        "category": "Village SLA Rules"
    },
    {
        "id": 4,
        "question": "How much financial subsidy is provided under the Gramin Housing Scheme?",
        "expected_answer": "Rs 1,20,000 for plain areas and Rs 1,30,000 for hilly areas",
        "expected_status": "N/A",
        "category": "Government Schemes"
    },
    {
        "id": 5,
        "question": "When will the government construct a new international airport in Chandanpur village?",
        "expected_answer": "ABSTAIN",
        "expected_status": "INSUFFICIENT_EVIDENCE",
        "category": "Out-of-domain / Unsupported Question"
    },
    {
        "id": 6,
        "question": "What are the door-to-door garbage collection timings in Gram Panchayat Chandanpur?",
        "expected_answer": "7:00 AM to 10:00 AM daily",
        "expected_status": "N/A",
        "category": "Village Services"
    }
]

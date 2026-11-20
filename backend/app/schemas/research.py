from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ResearchMetricsOut(BaseModel):
    id: int
    run_id: str
    config_type: str  # STANDALONE_LLM / RAG_LLM / RAG_VERIFICATION
    factual_accuracy: float
    hallucination_rate: float
    faithfulness: float
    retrieval_recall: float
    precision: float
    recall: float
    f1_score: float
    abstention_accuracy: float
    avg_latency: float
    timestamp: datetime

    class Config:
        from_attributes = True

class BenchmarkItemOut(BaseModel):
    id: int
    question: str
    expected_answer: str
    expected_status: str
    config_a_answer: str
    config_a_verdict: str
    config_b_answer: str
    config_b_verdict: str
    config_c_answer: str
    config_c_verdict: str

class ResearchRunResponse(BaseModel):
    run_id: str
    status: str
    results: List[ResearchMetricsOut]
    benchmarks: List[BenchmarkItemOut] = []

export interface ResearchMetricItem {
  id: number;
  run_id: string;
  config_type: 'STANDALONE_LLM' | 'RAG_LLM' | 'RAG_VERIFICATION';
  factual_accuracy: number;
  hallucination_rate: number;
  faithfulness: number;
  retrieval_recall: number;
  precision: number;
  recall: number;
  f1_score: number;
  abstention_accuracy: number;
  avg_latency: number;
  timestamp: string;
}

export interface BenchmarkItem {
  id: number;
  question: string;
  expected_answer: string;
  expected_status: string;
  config_a_answer: string;
  config_a_verdict: string;
  config_b_answer: string;
  config_b_verdict: string;
  config_c_answer: string;
  config_c_verdict: string;
}

export interface ResearchExperimentResponse {
  run_id: string;
  status: string;
  results: ResearchMetricItem[];
  benchmarks: BenchmarkItem[];
}

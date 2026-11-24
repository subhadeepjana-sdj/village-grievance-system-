import api from './api';

export interface AdminStatistics {
  summary: {
    total_users: number;
    total_complaints: number;
    pending_complaints: number;
    in_progress_complaints: number;
    resolved_complaints: number;
    total_documents: number;
  };
  ai_statistics: {
    total_ai_questions: number;
    supported_percentage: number;
    contradicted_percentage: number;
    abstain_percentage: number;
    average_confidence: number;
    average_response_time: number;
  };
}

export interface VerificationOverviewStats {
  total_interactions: number;
  total_claims_verified: number;
  supported_claims: number;
  contradicted_claims: number;
  insufficient_claims: number;
  total_corrections: number;
  total_abstentions: number;
  avg_confidence: number;
  avg_latency: number;
  verification_pass_rate: number;
  claim_distribution: {
    SUPPORTED: number;
    CONTRADICTED: number;
    INSUFFICIENT_EVIDENCE: number;
  };
  decision_distribution: {
    SHOW: number;
    CORRECT: number;
    ABSTAIN: number;
  };
}

export interface InteractionListItem {
  id: number;
  query_id: number;
  question: string;
  final_answer: string;
  decision: string;
  verification_status: string;
  confidence: number;
  processing_time: number;
  configuration: string;
  claim_count: number;
  supported_count: number;
  contradicted_count: number;
  insufficient_count: number;
  had_correction: boolean;
  is_abstained: boolean;
  created_at: string;
}

export interface PaginatedInteractions {
  total: number;
  page: number;
  page_size: number;
  items: InteractionListItem[];
}

export interface InteractionDetail {
  interaction_id: number;
  query_id: number;
  user_id?: number;
  question: string;
  timestamp: string;
  configuration: string;
  decision: string;
  confidence: number;
  processing_time: number;
  question_1_raw_generation: {
    raw_candidate_answer: string;
    configuration: string;
    had_regeneration: boolean;
  };
  question_2_extracted_claims: Array<{
    claim_id: string;
    db_id: number;
    claim_text: string;
    verification_result: string;
    confidence: number;
    matched_evidence?: string;
    reason?: string;
  }>;
  question_3_retrieved_evidence: Array<{
    id: number;
    source_type: string;
    document_id?: number;
    chunk_id?: string;
    similarity_score?: number;
    evidence_text: string;
  }>;
  question_4_supported_claims: any[];
  question_5_contradicted_claims: any[];
  question_6_insufficient_evidence_claims: any[];
  question_7_corrections_made: {
    correction_attempts_count: number;
    history: any[];
    delivered_final_answer: string;
    decision: string;
  };
  citations: any[];
}

export interface FeedbackPayload {
  response_id: number;
  claim_id?: number;
  feedback_type: string;
  corrected_verdict?: string;
  notes: string;
}

export const adminService = {
  getStatistics: async (): Promise<AdminStatistics> => {
    const res = await api.get<AdminStatistics>('/admin/statistics');
    return res.data;
  },

  // Feature 8 — AI Verification Center APIs
  getVerificationOverview: async (): Promise<VerificationOverviewStats> => {
    const res = await api.get<VerificationOverviewStats>('/admin/verification/overview');
    return res.data;
  },

  listInteractions: async (params?: { page?: number; page_size?: number; decision?: string; search?: string }): Promise<PaginatedInteractions> => {
    const res = await api.get<PaginatedInteractions>('/admin/verification/interactions', { params });
    return res.data;
  },

  getInteractionDetail: async (id: number): Promise<InteractionDetail> => {
    const res = await api.get<InteractionDetail>(`/admin/verification/interactions/${id}`);
    return res.data;
  },

  getClaimDetail: async (id: number): Promise<any> => {
    const res = await api.get(`/admin/verification/claims/${id}`);
    return res.data;
  },

  getEvidenceDetail: async (id: number): Promise<any> => {
    const res = await api.get(`/admin/verification/evidence/${id}`);
    return res.data;
  },

  getCorrectionHistory: async (responseId: number): Promise<any[]> => {
    const res = await api.get(`/admin/verification/corrections/${responseId}`);
    return res.data;
  },

  getReports: async (limit: number = 20): Promise<any[]> => {
    const res = await api.get('/admin/verification/reports', { params: { limit } });
    return res.data;
  },

  submitFeedback: async (payload: FeedbackPayload): Promise<any> => {
    const res = await api.post('/admin/verification/feedback', payload);
    return res.data;
  }
};

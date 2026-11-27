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

// Feature 9 — AI Feedback & Error Review Types
export type CitizenFeedbackType = 'HELPFUL' | 'INCORRECT' | 'INCOMPLETE' | 'MISLEADING';
export type FeedbackStatus = 'PENDING' | 'REVIEWING' | 'RESOLVED';
export type RootCauseCategory =
  | 'RETRIEVAL'
  | 'OUTDATED_DOCUMENT'
  | 'MODEL_GENERATION'
  | 'VERIFICATION_FAILURE'
  | 'OTHER';

export interface FeedbackReviewItem {
  id: number;
  feedback_id: number;
  admin_id?: number;
  root_cause: RootCauseCategory;
  corrective_action?: string;
  resolution_notes?: string;
  resolved_at?: string;
  created_at?: string;
}

export interface CitizenFeedbackItem {
  id: number;
  response_id: number;
  user_id?: number;
  feedback_type: CitizenFeedbackType;
  description?: string;
  status: FeedbackStatus;
  created_at?: string;
  updated_at?: string;
  reviews: FeedbackReviewItem[];
}

export interface FeedbackStats {
  total_feedback: number;
  pending_count: number;
  reviewing_count: number;
  resolved_count: number;
  resolution_rate: number;
  by_feedback_type: Record<string, number>;
  by_root_cause: Record<string, number>;
}

// Feature 10 — Knowledge Base Management Types
export interface DocumentVersionItem {
  id: number;
  document_id: number;
  version_number: number;
  file_path: string;
  file_hash?: string;
  file_size_bytes?: number;
  status: string;
  change_summary?: string;
  rejection_reason?: string;
  effective_from?: string;
  effective_until?: string;
  created_at?: string;
  approved_at?: string;
  processing_job?: {
    id: number;
    version_id: number;
    extraction_status: string;
    embedding_status: string;
    indexing_status: string;
    chunks_extracted?: number;
    chunks_embedded?: number;
    chunks_indexed?: number;
    error_stage?: string;
    error_message?: string;
  };
}

export interface KBStats {
  total_documents: number;
  total_versions: number;
  published_versions: number;
  pending_approval: number;
  processing: number;
  failed_processing: number;
  expiring_within_30_days: number;
  expired: number;
}

// Feature 11 — Audit Logs Types
export interface AuditEventItem {
  id: number;
  trace_id: string;
  actor_id?: number;
  actor_role?: string;
  event_type: string;
  action: string;
  entity_type?: string;
  entity_id?: string;
  old_value?: string;
  new_value?: string;
  description?: string;
  ip_address?: string;
  created_at?: string;
}

export interface AIRequestAuditItem {
  id: number;
  trace_id: string;
  query_id: number;
  model_name?: string;
  model_version?: string;
  prompt_version?: string;
  embedding_model?: string;
  total_claims?: number;
  supported_claims?: number;
  contradicted_claims?: number;
  insufficient_claims?: number;
  final_decision?: string;
  correction_attempts?: number;
  abstention_reason?: string;
  response_time_ms?: number;
  created_at?: string;
}

// Feature 12 — Model & RAG Management Types
export interface ModelConfigItem {
  id: number;
  name: string;
  version: string;
  provider: string;
  model_identifier: string;
  temperature: number;
  max_tokens: number;
  status: 'TESTING' | 'ACTIVE' | 'RETIRED';
  description?: string;
  activated_at?: string;
  created_at?: string;
}

export interface RAGConfigItem {
  id: number;
  name: string;
  version: string;
  embedding_model: string;
  top_k: number;
  chunk_size: number;
  chunk_overlap: number;
  similarity_threshold: number;
  reranking_enabled: number;
  status: 'TESTING' | 'ACTIVE' | 'RETIRED';
  description?: string;
  activated_at?: string;
  created_at?: string;
}

export interface VerificationConfigItem {
  id: number;
  name: string;
  version: string;
  nli_model: string;
  supported_threshold: number;
  contradiction_threshold: number;
  max_retries: number;
  abstention_enabled: number;
  status: 'TESTING' | 'ACTIVE' | 'RETIRED';
  description?: string;
  activated_at?: string;
  created_at?: string;
}

export interface ActiveConfigBundle {
  active_model?: ModelConfigItem;
  active_rag?: RAGConfigItem;
  active_verification?: VerificationConfigItem;
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
  },

  // Feature 9 — AI Feedback & Error Review APIs
  submitCitizenFeedback: async (payload: {
    response_id: number;
    feedback_type: CitizenFeedbackType;
    description?: string;
  }): Promise<CitizenFeedbackItem> => {
    const res = await api.post<CitizenFeedbackItem>('/feedback', payload);
    return res.data;
  },

  getMyFeedback: async (): Promise<CitizenFeedbackItem[]> => {
    const res = await api.get<CitizenFeedbackItem[]>('/feedback/my');
    return res.data;
  },

  listAdminFeedback: async (params?: {
    page?: number;
    page_size?: number;
    status?: FeedbackStatus;
    feedback_type?: CitizenFeedbackType;
    root_cause?: RootCauseCategory;
  }): Promise<{ items: CitizenFeedbackItem[]; total: number; page: number; page_size: number; pages: number }> => {
    const res = await api.get('/admin/feedback', { params });
    return res.data;
  },

  getFeedbackStats: async (): Promise<FeedbackStats> => {
    const res = await api.get<FeedbackStats>('/admin/feedback/stats');
    return res.data;
  },

  getFeedbackDetail: async (id: number): Promise<any> => {
    const res = await api.get(`/admin/feedback/${id}`);
    return res.data;
  },

  reviewFeedback: async (
    id: number,
    payload: {
      status: FeedbackStatus;
      root_cause: RootCauseCategory;
      corrective_action?: string;
      resolution_notes?: string;
    }
  ): Promise<CitizenFeedbackItem> => {
    const res = await api.put<CitizenFeedbackItem>(`/admin/feedback/${id}/review`, payload);
    return res.data;
  },

  // Feature 10 — Knowledge Base Management APIs
  uploadDocumentVersion: async (docId: number, formData: FormData): Promise<DocumentVersionItem> => {
    const res = await api.post<DocumentVersionItem>(`/admin/kb/documents/${docId}/versions`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  listDocumentVersions: async (
    docId: number,
    params?: { page?: number; page_size?: number; status?: string }
  ): Promise<{ items: DocumentVersionItem[]; total: number; page: number; page_size: number; pages: number }> => {
    const res = await api.get(`/admin/kb/documents/${docId}/versions`, { params });
    return res.data;
  },

  getDocumentVersion: async (versionId: number): Promise<DocumentVersionItem> => {
    const res = await api.get<DocumentVersionItem>(`/admin/kb/versions/${versionId}`);
    return res.data;
  },

  approveDocumentVersion: async (
    versionId: number,
    payload: { effective_from?: string; effective_until?: string } = {}
  ): Promise<DocumentVersionItem> => {
    const res = await api.put<DocumentVersionItem>(`/admin/kb/versions/${versionId}/approve`, payload);
    return res.data;
  },

  rejectDocumentVersion: async (versionId: number, reason: string): Promise<DocumentVersionItem> => {
    const res = await api.put<DocumentVersionItem>(`/admin/kb/versions/${versionId}/reject`, { reason });
    return res.data;
  },

  reindexDocumentVersion: async (versionId: number): Promise<DocumentVersionItem> => {
    const res = await api.post<DocumentVersionItem>(`/admin/kb/versions/${versionId}/reindex`);
    return res.data;
  },

  getExpiringDocuments: async (days: number = 30): Promise<any[]> => {
    const res = await api.get('/admin/kb/expiring', { params: { days } });
    return res.data;
  },

  getKBStats: async (): Promise<KBStats> => {
    const res = await api.get<KBStats>('/admin/kb/stats');
    return res.data;
  },

  // Feature 11 — Audit Logs APIs
  listAuditEvents: async (params?: {
    page?: number;
    page_size?: number;
    event_type?: string;
    action?: string;
    entity_type?: string;
    entity_id?: string;
    actor_id?: number;
    date_from?: string;
    date_to?: string;
  }): Promise<{ items: AuditEventItem[]; total: number; page: number; page_size: number; pages: number }> => {
    const res = await api.get('/admin/audit/events', { params });
    return res.data;
  },

  getAuditTrace: async (traceId: string): Promise<{ trace_id: string; events: AuditEventItem[]; ai_request_audit?: AIRequestAuditItem }> => {
    const res = await api.get(`/admin/audit/events/trace/${traceId}`);
    return res.data;
  },

  listAIRequestAudits: async (params?: {
    page?: number;
    page_size?: number;
    final_decision?: string;
    model_name?: string;
  }): Promise<{ items: AIRequestAuditItem[]; total: number; page: number; page_size: number; pages: number }> => {
    const res = await api.get('/admin/audit/ai-requests', { params });
    return res.data;
  },

  getAIRequestAudit: async (auditId: number): Promise<AIRequestAuditItem> => {
    const res = await api.get<AIRequestAuditItem>(`/admin/audit/ai-requests/${auditId}`);
    return res.data;
  },

  getAuditStats: async (): Promise<any> => {
    const res = await api.get('/admin/audit/stats');
    return res.data;
  },

  getMongoDBStatus: async (): Promise<any> => {
    const res = await api.get('/admin/audit/mongodb-status');
    return res.data;
  },

  // Feature 12 — Model & RAG Management APIs
  listModels: async (status?: string): Promise<ModelConfigItem[]> => {
    const res = await api.get<ModelConfigItem[]>('/admin/models', { params: { status } });
    return res.data;
  },

  registerModel: async (payload: {
    name: string;
    version?: string;
    provider: string;
    model_identifier: string;
    temperature?: number;
    max_tokens?: number;
    description?: string;
  }): Promise<ModelConfigItem> => {
    const res = await api.post<ModelConfigItem>('/admin/models', payload);
    return res.data;
  },

  activateModel: async (modelId: number): Promise<ModelConfigItem> => {
    const res = await api.put<ModelConfigItem>(`/admin/models/${modelId}/activate`);
    return res.data;
  },

  listRAGConfigs: async (status?: string): Promise<RAGConfigItem[]> => {
    const res = await api.get<RAGConfigItem[]>('/admin/rag-config', { params: { status } });
    return res.data;
  },

  getActiveConfigBundle: async (): Promise<ActiveConfigBundle> => {
    const res = await api.get<ActiveConfigBundle>('/admin/rag-config/active');
    return res.data;
  },

  createRAGConfig: async (payload: {
    name: string;
    version?: string;
    embedding_model?: string;
    top_k?: number;
    chunk_size?: number;
    chunk_overlap?: number;
    similarity_threshold?: number;
    reranking_enabled?: boolean;
    description?: string;
  }): Promise<RAGConfigItem> => {
    const res = await api.post<RAGConfigItem>('/admin/rag-config', payload);
    return res.data;
  },

  listVerificationConfigs: async (status?: string): Promise<VerificationConfigItem[]> => {
    const res = await api.get<VerificationConfigItem[]>('/admin/verification-config', { params: { status } });
    return res.data;
  },

  createVerificationConfig: async (payload: {
    name: string;
    version?: string;
    nli_model?: string;
    supported_threshold?: number;
    contradiction_threshold?: number;
    max_retries?: number;
    abstention_enabled?: boolean;
    description?: string;
  }): Promise<VerificationConfigItem> => {
    const res = await api.post<VerificationConfigItem>('/admin/verification-config', payload);
    return res.data;
  },

  evaluateConfig: async (
    configType: 'MODEL' | 'RAG' | 'VERIFICATION',
    configId: number,
    payload: {
      evaluation_dataset?: string;
      factual_accuracy: number;
      hallucination_rate: number;
      faithfulness: number;
      abstention_accuracy?: number;
      avg_latency_ms?: number;
      notes?: string;
    }
  ): Promise<any> => {
    const res = await api.post(`/admin/configs/${configType}/${configId}/evaluate`, payload);
    return res.data;
  },

  approveConfig: async (
    configType: 'MODEL' | 'RAG' | 'VERIFICATION',
    configId: number,
    notes?: string
  ): Promise<any> => {
    const res = await api.put(`/admin/configs/${configType}/${configId}/approve`, { notes });
    return res.data;
  },

  // Notifications & Alerts Centre
  listNotifications: async (params?: {
    filter?: string;
    category?: string;
    severity?: string;
    search?: string;
    date_from?: string;
    date_to?: string;
    include_dismissed?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<NotificationListResponse> => {
    const res = await api.get<NotificationListResponse>('/admin/notifications', { params });
    return res.data;
  },

  getNotificationUnreadCount: async (): Promise<NotificationUnreadCount> => {
    const res = await api.get<NotificationUnreadCount>('/admin/notifications/unread-count');
    return res.data;
  },

  setNotificationRead: async (id: string, is_read = true): Promise<NotificationItem> => {
    const res = await api.patch<NotificationItem>(`/admin/notifications/${encodeURIComponent(id)}/read`, { is_read });
    return res.data;
  },

  acknowledgeNotification: async (id: string): Promise<NotificationItem> => {
    const res = await api.patch<NotificationItem>(`/admin/notifications/${encodeURIComponent(id)}/acknowledge`);
    return res.data;
  },

  dismissNotification: async (id: string): Promise<NotificationItem> => {
    const res = await api.patch<NotificationItem>(`/admin/notifications/${encodeURIComponent(id)}/dismiss`);
    return res.data;
  },

  markAllNotificationsRead: async (): Promise<{ marked_read: number }> => {
    const res = await api.patch<{ marked_read: number }>('/admin/notifications/mark-all-read');
    return res.data;
  },

  scanNotificationSLA: async (): Promise<NotificationUnreadCount & { alerts_processed: number }> => {
    const res = await api.post<NotificationUnreadCount & { alerts_processed: number }>('/admin/notifications/scan-sla');
    return res.data;
  },

  getNotificationDigest: async (): Promise<DailyDigestSummary> => {
    const res = await api.get<DailyDigestSummary>('/admin/notifications/digest');
    return res.data;
  },

  getNotificationPreferences: async (): Promise<NotificationPreferences> => {
    const res = await api.get<NotificationPreferences>('/admin/notifications/preferences');
    return res.data;
  },

  updateNotificationPreferences: async (
    payload: Partial<NotificationPreferences>
  ): Promise<NotificationPreferences> => {
    const res = await api.put<NotificationPreferences>('/admin/notifications/preferences', payload);
    return res.data;
  },
};

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  category: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | string;
  recipient_id?: number;
  recipient_role?: string;
  related_complaint_id?: number;
  related_complaint_number?: string;
  group_key?: string;
  occurrence_count: number;
  action_url?: string;
  action_label?: string;
  metadata?: Record<string, any>;
  is_read: boolean;
  requires_action: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  created_at: string;
  updated_at?: string;
  read_at?: string;
  dismissed_at?: string;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  unread_count: number;
  critical_count: number;
  pending_action_count: number;
}

export interface NotificationUnreadCount {
  unread_count: number;
  critical_count: number;
  pending_action_count: number;
}

export interface DailyDigestSummary {
  generated_at: string;
  pending_complaints: number;
  overdue_complaints: number;
  ai_verification_issues: number;
  pending_feedback_reviews: number;
  unread_notifications: number;
  critical_unread_notifications: number;
  highlights: string[];
}

export interface NotificationPreferences {
  user_id: number;
  enabled_categories: string[];
  min_severity: 'INFO' | 'WARNING' | 'CRITICAL' | string;
  in_app_enabled: boolean;
  email_digest_enabled: boolean;
  sms_critical_enabled: boolean;
  smart_grouping_enabled: boolean;
  auto_escalation_enabled: boolean;
  escalation_sla_hours: number;
  updated_at?: string;
}

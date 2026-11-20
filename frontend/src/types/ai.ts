export type VerificationDecision = 'SHOW' | 'CORRECT' | 'ABSTAIN';

export type VerificationStatus = 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE' | 'VERIFYING';

export type PipelineConfiguration = 'baseline' | 'rag' | 'rag_verification';

export interface EvidenceItem {
  document_id?: number;
  chunk_id?: string;
  similarity_score?: number;
  evidence_text: string;
  source_type: string;
  metadata?: {
    source?: string;
    department?: string;
    category?: string;
    page_number?: number;
  };
}

export interface ClaimVerification {
  claim: string;
  evidence?: string;
  verification_result: 'SUPPORTED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE';
  confidence: number;
  reason?: string;
}

export interface AIResponseData {
  id: number;
  question: string;
  answer: string;
  decision: VerificationDecision;
  verification_status: VerificationStatus;
  confidence: number;
  processing_time: number;
  configuration: PipelineConfiguration;
  created_at: string;
  evidences: EvidenceItem[];
  verification_results: ClaimVerification[];
}

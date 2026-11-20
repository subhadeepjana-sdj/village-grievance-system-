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

export const adminService = {
  getStatistics: async (): Promise<AdminStatistics> => {
    const res = await api.get<AdminStatistics>('/admin/statistics');
    return res.data;
  }
};

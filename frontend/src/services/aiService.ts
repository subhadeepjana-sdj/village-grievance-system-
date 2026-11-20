import api from './api';
import { AIResponseData, PipelineConfiguration } from '../types';

export const aiService = {
  queryAI: async (question: string, configuration: PipelineConfiguration = 'rag_verification'): Promise<AIResponseData> => {
    const res = await api.post<AIResponseData>('/ai/query', {
      question,
      configuration
    });
    return res.data;
  },

  getAIHistory: async (): Promise<AIResponseData[]> => {
    const res = await api.get<AIResponseData[]>('/ai/history');
    return res.data;
  }
};

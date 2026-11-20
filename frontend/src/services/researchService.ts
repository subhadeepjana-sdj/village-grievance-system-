import api from './api';
import { ResearchMetricItem, ResearchExperimentResponse } from '../types';

export const researchService = {
  getLatestMetrics: async (): Promise<ResearchMetricItem[]> => {
    const res = await api.get<ResearchMetricItem[]>('/research/metrics');
    return res.data;
  },

  runExperiment: async (): Promise<ResearchExperimentResponse> => {
    const res = await api.post<ResearchExperimentResponse>('/research/run');
    return res.data;
  }
};

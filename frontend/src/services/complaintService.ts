import api from './api';
import { Complaint, ComplaintStatusHistoryItem } from '../types';

export const complaintService = {
  getComplaints: async (statusFilter?: string, categoryFilter?: string): Promise<Complaint[]> => {
    const params: Record<string, string> = {};
    if (statusFilter) params.status_filter = statusFilter;
    if (categoryFilter) params.category_filter = categoryFilter;

    const res = await api.get<Complaint[]>('/complaints', { params });
    return res.data;
  },

  getComplaintById: async (id: string | number): Promise<Complaint> => {
    const res = await api.get<Complaint>(`/complaints/${id}`);
    return res.data;
  },

  submitComplaint: async (formData: FormData): Promise<Complaint> => {
    const res = await api.post<Complaint>('/complaints', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return res.data;
  },

  updateComplaintStatus: async (
    id: number,
    data: { status?: string; department_id?: number; priority?: string; remarks?: string }
  ): Promise<Complaint> => {
    const res = await api.patch<Complaint>(`/complaints/${id}`, data);
    return res.data;
  },

  getComplaintHistory: async (id: number): Promise<ComplaintStatusHistoryItem[]> => {
    const res = await api.get<ComplaintStatusHistoryItem[]>(`/complaints/${id}/history`);
    return res.data;
  }
};

export interface DocumentItem {
  id: number;
  title: string;
  file_path: string;
  document_type: string;
  source?: string;
  department?: string;
  village?: string;
  version: string;
  effective_date?: string;
  uploaded_by?: string;
  created_at: string;
}

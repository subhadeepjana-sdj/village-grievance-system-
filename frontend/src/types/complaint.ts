export type ComplaintStatus = 
  | 'SUBMITTED' 
  | 'ACKNOWLEDGED' 
  | 'ASSIGNED' 
  | 'UNDER_REVIEW' 
  | 'IN_PROGRESS' 
  | 'RESOLVED' 
  | 'REJECTED' 
  | 'CLOSED';

export type ComplaintPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface ComplaintStatusHistoryItem {
  id: number;
  old_status?: string;
  new_status: string;
  changed_by: string;
  remarks?: string;
  timestamp: string;
}

export interface Complaint {
  id: number;
  complaint_number: string;
  user_id: number;
  village_id?: number;
  department_id?: number;
  category: string;
  title: string;
  description: string;
  location?: string;
  status: ComplaintStatus;
  priority: ComplaintPriority;
  file_path?: string;
  created_at: string;
  updated_at: string;
  citizen_name?: string;
  department_name?: string;
  village_name?: string;
  history?: ComplaintStatusHistoryItem[];
}

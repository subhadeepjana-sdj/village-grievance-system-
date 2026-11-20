export type UserRole = 
  | 'CITIZEN' 
  | 'PANCHAYAT_STAFF' 
  | 'DEPARTMENT_OFFICIAL' 
  | 'ADMIN' 
  | 'RESEARCHER';

export interface User {
  id: number;
  name: string;
  email: string;
  phone?: string;
  role: UserRole;
  village_id?: number;
  department_id?: number;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  user_id: number;
  name: string;
  email: string;
}

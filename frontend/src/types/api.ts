// TypeScript type definitions for BIM Project Management API

export interface Project {
  project_id: number;
  project_name: string;
  project_number?: string;
  client_id?: number;
  client_name?: string;
  type_id?: number;
  type_name?: string;
  project_type?: string; // Alternative field name used by backend
  status?: string;
  priority?: string;
  start_date?: string;
  end_date?: string;
  area_hectares?: number;
  mw_capacity?: number;
  address?: string;
  city?: string;
  state?: string;
  postcode?: string;
  folder_path?: string;
  ifc_folder_path?: string;
  description?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ReviewCycle {
  cycle_id: number;
  project_id: number;
  stage?: string;
  fee?: number;
  assigned_users?: string;
  reviews_per_phase?: string;
  planned_start_date?: string;
  planned_completion_date?: string;
  actual_start_date?: string;
  actual_completion_date?: string;
  hold_date?: string;
  resume_date?: string;
  new_contract?: boolean;
  status?: string;
}

export interface Review {
  review_id: number;
  project_id: number;
  cycle_id: number;
  review_date: string;
  status?: string;
  assigned_to?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  task_id: number;
  project_id: number;
  task_name: string;
  description?: string;
  assigned_to?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  completed_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Client {
  client_id: number;
  client_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  created_at?: string;
}

export interface ProjectType {
  project_type_id: number;
  project_type_name: string;
  description?: string;
}

export interface User {
  user_id: number;
  username: string;
  full_name?: string;
  email?: string;
  role?: string;
  created_at?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Filter and Query types
export interface ProjectFilters {
  search?: string;
  client_id?: number;
  type_id?: number;
  status?: string;
  start_date_from?: string;
  start_date_to?: string;
}

export interface ReviewFilters {
  project_id?: number;
  cycle_id?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
}

export interface TaskFilters {
  project_id?: number;
  assigned_to?: string;
  status?: string;
  priority?: string;
  due_date_from?: string;
  due_date_to?: string;
}

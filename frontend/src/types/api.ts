// TypeScript type definitions for BIM Project Management API

export interface Project {
  project_id: number;
  project_name: string;
  project_number?: string;
  contract_number?: string;
  client_id?: number | null;
  client_name?: string;
  type_id?: number;
  type_name?: string;
  project_type?: string; // Alternative field name used by backend
  status?: string;
  priority?: string | number;
  priority_label?: string;
  start_date?: string;
  end_date?: string;
  area_hectares?: number | null;
  mw_capacity?: number | null;
  address?: string;
  city?: string;
  state?: string;
  postcode?: string;
  folder_path?: string;
  ifc_folder_path?: string;
  description?: string;
  internal_lead?: number | null;
  naming_convention?: string | null;
  created_at?: string;
  updated_at?: string;
  total_service_agreed_fee?: number;
  total_service_billed_amount?: number;
  service_billed_pct?: number;
  agreed_fee?: number;
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

export interface DashboardTimelineReviewItem {
  review_id: number;
  planned_date?: string | null;
  due_date?: string | null;
  status?: string | null;
  service_name?: string | null;
}

export interface DashboardTimelineProject {
  project_id: number;
  project_name: string;
  start_date?: string | null;
  end_date?: string | null;
  project_manager?: string | null;
  client_id?: number | null;
  client_name?: string | null;
  type_id?: number | null;
  project_type?: string | null;
  review_items: DashboardTimelineReviewItem[];
}

export interface DashboardTimelineResponse {
  projects: DashboardTimelineProject[];
  date_range?: {
    min: string;
    max: string;
  } | null;
}

export interface TaskItem {
  label?: string;
  title?: string;
  completed?: boolean;
  notes?: string;
  [key: string]: unknown;
}

export interface Task {
  task_id: number;
  project_id: number;
  project_name?: string;
  task_name: string;
  cycle_id?: number | null;
  task_date?: string | null;
  time_start?: string | null;
  time_end?: string | null;
  time_spent_minutes?: number | null;
  status?: string | null;
  assigned_to?: number | null;
  assigned_to_name?: string | null;
  task_items?: TaskItem[];
  notes?: string | null;
  description?: string | null;
  priority?: string | null;
  due_date?: string | null;
  completed_date?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface TaskPayload {
  task_name: string;
  project_id: number;
  cycle_id?: number | null;
  task_date?: string | null;
  time_start?: string | null;
  time_end?: string | null;
  time_spent_minutes?: number | null;
  assigned_to?: number | null;
  status?: string | null;
  task_items?: TaskItem[];
  notes?: string | null;
}

export interface Client {
  id?: number;
  client_id: number;
  client_name: string;
  name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  city?: string;
  state?: string;
  postcode?: string;
  country?: string;
  naming_convention?: string | null;
  created_at?: string;
}

export interface ProjectType {
  project_type_id: number;
  project_type_name: string;
  description?: string;
}

export interface User {
  user_id: number;
  name?: string;
  username?: string;
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
  user_id?: number;
  assigned_to?: number;
  date_from?: string;
  date_to?: string;
  limit?: number;
  page?: number;
}

export interface PaginatedResult<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  meta?: Record<string, unknown>;
}

export interface ServiceTemplate {
  id: number;
  template_name: string;
  description: string;
  service_type: string;
  parameters: any;
  created_by: number;
  created_at: string;
  is_active: boolean;
}

export interface ProjectService {
  service_id: number;
  project_id: number;
  phase?: string;
  service_code: string;
  service_name: string;
  unit_type?: string;
  unit_qty?: number;
  unit_rate?: number;
  lump_sum_fee?: number;
  agreed_fee?: number;
  bill_rule?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  status: string;
  progress_pct?: number;
  claimed_to_date?: number;
  billing_progress_pct?: number;
  billed_amount?: number;
  agreed_fee_remaining?: number;
}

export interface ServiceReview {
  review_id: number;
  service_id: number;
  cycle_no: number;
  planned_date: string;
  due_date?: string;
  disciplines?: string;
  deliverables?: string;
  status: string;
  weight_factor?: number | null;
  invoice_reference?: string;
  evidence_links?: string;
  actual_issued_at?: string;
  source_phase?: string | null;
  billing_phase?: string | null;
  billing_rate?: number | null;
  billing_amount?: number | null;
  service_name?: string;
  service_phase?: string;
  is_billed?: boolean;
}

export interface ReviewBillingRecord extends ServiceReview {
  billing_date?: string | null;
}

export interface ReviewBillingPhaseSummary {
  billing_phase: string;
  source_phase: string;
  review_count: number;
  total_amount: number;
  slipped_count: number;
  slipped_amount: number;
}

export interface ReviewBillingMonthlySummary {
  period: string;
  review_count: number;
  total_amount: number;
}

export interface ReviewBillingResponse {
  reviews: ReviewBillingRecord[];
  summary_by_phase: ReviewBillingPhaseSummary[];
  monthly_totals: ReviewBillingMonthlySummary[];
  total_amount: number;
  total_reviews: number;
}

export interface ServiceItem {
  item_id: number;
  service_id: number;
  item_type: 'review' | 'audit' | 'deliverable' | 'milestone' | 'inspection' | 'meeting' | string;
  title: string;
  description?: string;
  planned_date?: string;
  due_date?: string;
  actual_date?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  assigned_to?: string;
  evidence_links?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  is_billed?: boolean;
}

export interface FileServiceTemplateSummary {
  total_items: number;
  lump_sum_items: number;
  review_items: number;
  total_reviews: number;
  estimated_value: number;
}

export interface FileServiceTemplate {
  key: string;
  index: number;
  name: string;
  sector?: string;
  notes?: string;
  description?: string;
  items: Record<string, any>[];
  summary: FileServiceTemplateSummary;
  is_valid: boolean;
  validation_errors: string[];
  source: 'file';
}

export interface FileServiceTemplatePayload {
  name: string;
  sector?: string;
  notes?: string;
  items: Record<string, any>[];
}

export interface ApplyTemplateDuplicate {
  service_code?: string;
  service_name?: string;
  phase?: string;
}

export interface ApplyTemplateSkipped extends ApplyTemplateDuplicate {
  reason?: string;
  details?: string[];
}

export interface ApplyTemplateResult {
  template_name: string;
  created: Array<Record<string, any>>;
  skipped: ApplyTemplateSkipped[];
  duplicates: ApplyTemplateDuplicate[];
  existing_services: number;
  replaced_services: number;
}

export interface ProjectAliasIssueSummary {
  total_issues: number;
  open_issues: number;
  alias_count?: number;
  aliases?: string;
  has_issues?: boolean;
}

export interface ProjectAlias {
  alias_name: string;
  project_id: number;
  project_name?: string;
  project_status?: string;
  project_manager?: string;
  project_created_at?: string | null;
  issue_summary: ProjectAliasIssueSummary;
}

export interface ProjectAliasStats {
  project_id: number;
  project_name: string;
  alias_count: number;
  aliases: string;
  total_issues: number;
  open_issues: number;
  has_issues: boolean;
}

export interface UnmappedProjectAlias {
  project_name: string;
  total_issues: number;
  open_issues: number;
  closed_issues: number;
  sources: number;
  first_issue_date?: string | null;
  last_issue_date?: string | null;
  suggested_match?: {
    project_name: string;
    match_type: string;
    confidence: number;
  } | null;
}

export interface ProjectAliasValidationResult {
  orphaned_aliases: Array<{ alias_name: string; invalid_project_id: number }>;
  duplicate_aliases: Array<{ alias_name: string; count: number }>;
  unused_projects: Array<{ project_id: number; project_name: string }>;
  mapping_conflicts: Array<Record<string, any>>;
  total_aliases: number;
  total_projects_with_aliases: number;
}

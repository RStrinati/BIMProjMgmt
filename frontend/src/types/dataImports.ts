/**
 * TypeScript type definitions for Data Imports API
 * Matches backend API responses from backend/app.py
 */

// ============================================================================
// ACC Desktop Connector Types
// ============================================================================

export interface ACCConnectorFolder {
  project_id: number;
  folder_path: string | null;
  exists: boolean;
}

export interface ACCConnectorFile {
  id: number;
  project_id: number;
  file_path: string;
  file_name: string;
  file_size: number | null;
  file_extension: string | null;
  date_modified: string | null;
  date_extracted: string;
  extracted_by: string | null;
}

export interface ACCConnectorFilesResponse {
  files: ACCConnectorFile[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ExtractACCFilesRequest {
  folder_path: string;
  file_types?: string[];
  recursive?: boolean;
}

export interface ExtractACCFilesResponse {
  success: boolean;
  files_extracted: number;
  folder_path: string;
  errors?: string[];
}

// ============================================================================
// ACC Data Import Types
// ============================================================================

export interface ACCImportLog {
  log_id: number;
  project_id: number;
  import_date: string;
  folder_name: string;
  status: string;
  summary: string;
}

export interface ACCImportLogsResponse {
  logs: ACCImportLog[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ACCImportRequest {
  file_path: string;
  import_type: 'csv' | 'zip' | 'folder';
}

export interface ACCImportResponse {
  success: boolean;
  project_id: number;
  folder_path: string;
  execution_time_seconds: number;
  message: string;
  records_imported?: number;
  import_type?: string;
  errors?: string[];
}

export interface ACCBookmark {
  id: number;
  project_id: number;
  bookmark_name: string;
  file_path: string;
  import_type: string;
  created_date: string;
  last_used: string | null;
}

// ============================================================================
// ACC Issues Types
// ============================================================================

export interface ACCIssue {
  id: number;
  project_id: number;
  issue_id: string;
  title: string;
  status: string;
  type: string;
  assigned_to: string | null;
  due_date: string | null;
  created_date: string;
  closed_date: string | null;
  description: string | null;
  location: string | null;
  custom_attributes: Record<string, any> | null;
}

export interface ACCIssuesResponse {
  issues: ACCIssue[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface ACCIssuesStats {
  total_issues: number;
  open_issues: number;
  closed_issues: number;
  overdue_issues: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_assigned_to: Record<string, number>;
}

export interface ACCIssuesFilters {
  status?: string;
  type?: string;
  assigned_to?: string;
  from_date?: string;
  to_date?: string;
  search?: string;
}

// ============================================================================
// Revizto Extraction Types
// ============================================================================

export interface ReviztoExtractionRun {
  id: number;
  run_id: string;
  project_id: number | null;
  export_folder: string;
  start_time: string;
  end_time: string | null;
  status: string;
  records_extracted: number | null;
  error_message: string | null;
  extracted_by: string | null;
}

export interface ReviztoExtractionRunsResponse {
  runs: ReviztoExtractionRun[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface StartReviztoExtractionRequest {
  project_id?: number;
  export_folder: string;
}

export interface StartReviztoExtractionResponse {
  success: boolean;
  run_id: string;
  export_folder: string;
}

// ============================================================================
// Revit Health Check Types
// ============================================================================

export interface RevitHealthFile {
  id: number;
  project_id: number;
  file_name: string;
  file_path: string;
  check_date: string;
  health_score: number | null;
  total_warnings: number | null;
  total_errors: number | null;
  file_size_mb: number | null;
  uploaded_by: string | null;
}

export interface RevitHealthFilesResponse {
  files: RevitHealthFile[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface RevitHealthSummary {
  total_files: number;
  avg_health_score: number;
  total_warnings: number;
  total_errors: number;
  latest_check_date: string | null;
  files_by_score: Record<string, number>;
}

export interface RevitHealthServiceTemplate {
  id: number;
  template_name: string;
  warning_threshold: number;
  error_threshold: number;
  check_categories: string[];
  is_active: boolean;
  created_date: string;
  updated_date: string | null;
}

// ============================================================================
// Control Model Configuration
// ============================================================================

export type ValidationTarget = 'naming' | 'coordinates' | 'levels';

export interface ControlModelMetadata {
  validation_targets: ValidationTarget[];
  is_primary?: boolean;
  volume_label?: string | null;
  notes?: string | null;
}

export interface ControlModel {
  id: number | null;
  file_name: string;
  is_active: boolean;
  metadata: ControlModelMetadata;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ControlModelConfiguration {
  project_id: number;
  available_models: string[];
  control_models: ControlModel[];
  primary_control_model: string | null;
  validation_summary: {
    naming_ready: boolean;
    coordinates_ready: boolean;
    levels_ready: boolean;
    multi_volume_ready: boolean;
    active_control_count: number;
    issues: string[];
  };
  mode: 'none' | 'single' | 'multi';
  validation_targets: ValidationTarget[];
  message?: string;
}

export interface ControlModelInput {
  file_name: string;
  validation_targets?: ValidationTarget[];
  volume_label?: string | null;
  notes?: string | null;
  is_primary?: boolean;
}

export interface ControlModelUpdateRequest {
  control_models: ControlModelInput[];
  primary_control_model?: string | null;
}

// ============================================================================
// Common Response Types
// ============================================================================

export interface ApiSuccessResponse {
  success: boolean;
  message?: string;
}

export interface ApiErrorResponse {
  error: string;
  details?: string;
}

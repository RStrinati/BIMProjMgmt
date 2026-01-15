// TypeScript type definitions for BIM Project Management API

export interface Project {
  project_id: number;
  project_name: string;
  project_number?: string;
  contract_number?: string;
  client_id?: number | null;
  client_name?: string;
  project_manager?: string | null;
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

export interface Bid {
  bid_id: number;
  project_id?: number | null;
  client_id?: number | null;
  bid_name: string;
  bid_type: 'PROPOSAL' | 'FEE_UPDATE' | 'VARIATION' | string;
  status: 'DRAFT' | 'SUBMITTED' | 'AWARDED' | 'LOST' | 'ARCHIVED' | string;
  probability?: number | null;
  owner_user_id?: number | null;
  currency_code?: string | null;
  stage_framework?: string | null;
  validity_days?: number | null;
  gst_included?: boolean | null;
  pi_notes?: string | null;
  created_at?: string;
  updated_at?: string;
  client_name?: string | null;
  owner_name?: string | null;
  project_name?: string | null;
}

export interface BidSection {
  bid_section_id: number;
  section_key: string;
  content_json?: string | Record<string, any> | null;
  sort_order?: number | null;
}

export interface BidScopeItem {
  scope_item_id: number;
  service_code?: string | null;
  title: string;
  description?: string | null;
  stage_name?: string | null;
  deliverables_json?: string | Record<string, any> | null;
  included_qty?: number | null;
  unit?: string | null;
  unit_rate?: number | null;
  lump_sum?: number | null;
  is_optional?: boolean | null;
  option_group?: string | null;
  sort_order?: number | null;
}

export interface BidScopeTemplateItem {
  phase?: string | null;
  service_code?: string | null;
  service_name?: string | null;
  unit_type?: string | null;
  default_units?: number | null;
  unit_rate?: number | null;
  lump_sum_fee?: number | null;
  notes?: string | null;
  deliverables?: string[] | string | null;
}

export interface BidScopeTemplate {
  name: string;
  sector?: string | null;
  notes?: string | null;
  items: BidScopeTemplateItem[];
}

export interface BidProgramStage {
  program_stage_id: number;
  stage_name: string;
  planned_start?: string | null;
  planned_end?: string | null;
  cadence?: string | null;
  cycles_planned?: number | null;
  sort_order?: number | null;
}

export interface BidBillingLine {
  billing_line_id: number;
  period_start: string;
  period_end: string;
  amount: number;
  notes?: string | null;
  sort_order?: number | null;
}

export interface BidAwardResult {
  project_id: number;
  created_services: number;
  created_reviews: number;
  created_claims: number;
  service_ids?: number[];
  review_ids?: number[];
  claim_ids?: number[];
  message?: string;
}

export interface BidVariation {
  variation_id: number;
  project_id: number;
  bid_id?: number | null;
  title: string;
  description?: string | null;
  baseline_contract_value?: number | null;
  remaining_value?: number | null;
  proposed_change_value: number;
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | string;
  created_at?: string;
  updated_at?: string;
}

export interface SchemaHealthReport {
  ok: boolean;
  missing_tables: string[];
  missing_columns: Record<string, string[]>;
  bid_module_ready: boolean;
  bid_missing_tables: string[];
  required_tables: string[];
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

export interface DashboardFilters {
  project_ids?: number[] | null;
  client_ids?: number[] | null;
  type_ids?: number[] | null;
  discipline?: string | null;
  status?: string | null;
  priority?: string | null;
  zone?: string | null;
  location?: string | null;
  manager?: string | null;
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
  priority?: string | number | null;
  priority_label?: string | null;
  internal_lead?: number | null;
  internal_lead_name?: string | null;
  lead_name?: string | null;
  progress_pct?: number | null;
  service_billed_pct?: number | null;
  total_service_billed_amount?: number | null;
  total_service_agreed_fee?: number | null;
  agreed_fee?: number | null;
  review_items: DashboardTimelineReviewItem[];
}

export interface DashboardTimelineResponse {
  projects: DashboardTimelineProject[];
  date_range?: {
    min: string;
    max: string;
  } | null;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface WarehouseDashboardMetrics {
  project_health: {
    projects?: number;
    open_issues?: number;
    high_priority_issues?: number;
    avg_resolution_days?: number | null;
    review_count?: number;
    completed_reviews?: number;
    overdue_reviews?: number;
    services_in_progress?: number;
    services_completed?: number;
    earned_value?: number;
    claimed_to_date?: number;
    variance_fee?: number;
  };
  issue_trends: Array<{
    date: string | null;
    open_issues: number;
    closed_issues: number;
    avg_backlog_days: number | null;
    avg_resolution_days: number | null;
    avg_urgency: number | null;
    avg_sentiment: number | null;
  }>;
  review_performance: {
    total_reviews?: number;
    completed_reviews?: number;
    overdue_reviews?: number;
    on_time_rate?: number | null;
    avg_planned_vs_actual_days?: number | null;
  };
  service_financials: {
    earned_value?: number;
    claimed_to_date?: number;
    variance_fee?: number;
    avg_progress_pct?: number | null;
  };
  backlog_age?: {
    bucket_0_7: number;
    bucket_8_30: number;
    bucket_31_90: number;
    bucket_90_plus: number;
    avg_age_days?: number | null;
  };
  control_models?: {
    projects_with_control_models: number;
    projects_missing: number;
  };
  data_freshness?: {
    revizto_last_run?: string | null;
    revizto_projects_extracted?: number | null;
    acc_last_import?: string | null;
    acc_last_import_project_id?: number | null;
  };
  data_quality?: {
    last_run_id?: number | null;
    last_run_status?: string | null;
    last_run_completed_at?: string | null;
    checks_total?: number;
    checks_failed?: number;
    checks_failed_high?: number;
    checks_failed_medium?: number;
  };
  error?: string;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface RevitHealthDashboardMetrics {
  summary: {
    total_files: number;
    projects: number;
    avg_health_score: number | null;
    min_health_score: number | null;
    max_health_score: number | null;
    good_files: number;
    fair_files: number;
    poor_files: number;
    critical_files: number;
    files_with_link_issues: number;
    total_warnings: number;
    total_critical_warnings: number;
    latest_check_date: string | null;
  };
  trend: Array<{
    year_month: string;
    avg_health_score: number | null;
    files: number;
  }>;
  categories?: {
    good: { count: number; pct: number | null };
    fair: { count: number; pct: number | null };
    poor: { count: number; pct: number | null };
    critical: { count: number; pct: number | null };
  };
  by_discipline?: Array<{
    discipline: string;
    discipline_full_name?: string | null;
    total_files: number;
    avg_health_score: number | null;
    total_warnings: number;
    total_critical_warnings: number;
    files_with_link_issues: number;
    good_files: number;
    fair_files: number;
    poor_files: number;
    critical_files: number;
  }>;
  top_files?: Array<{
    file_name: string;
    project_id: number | null;
    discipline: string | null;
    discipline_full_name?: string | null;
    health_score: number | null;
    health_category: string | null;
    total_warnings: number | null;
    critical_warnings: number | null;
    link_health_flag: string | null;
    export_datetime: string | null;
  }>;
  error?: string;
  filters?: DashboardFilters;
  as_of?: string | null;
  sections?: {
    file_naming?: NamingComplianceMetrics;
    coordinates?: {
      total: number;
      compliant: number;
      non_compliant: number;
      missing_control: number;
      as_of?: string | null;
    };
    grids?: {
      total: number;
      aligned: number;
      slight_deviation: number;
      not_aligned: number;
      additional_grids: number;
      missing_grids: number;
      as_of?: string | null;
    };
    levels?: {
      total: number;
      aligned: number;
      not_aligned: number;
      as_of?: string | null;
    };
  };
}

export interface NamingComplianceMetrics {
  summary: {
    total_files: number;
    valid_files: number;
    invalid_files: number;
    compliance_pct: number | null;
    latest_validated: string | null;
  };
  by_discipline: Array<{
    discipline: string;
    total_files: number;
    valid_files: number;
    invalid_files: number;
    valid_pct: number | null;
  }>;
  recent_invalid: Array<{
    file_name: string;
    project_name: string | null;
    discipline_code?: string | null;
    discipline: string | null;
    validation_status: string | null;
    validation_reason: string | null;
    failed_field_name: string | null;
    failed_field_value: string | null;
    failed_field_reason: string | null;
    validated_date: string | null;
  }>;
  error?: string;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface IssueHistoryPoint {
  week_start: string | null;
  status: string;
  count: number;
}

export interface IssuesHistoryResponse {
  items: IssueHistoryPoint[];
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface DashboardIssuesKpis {
  total_issues: number;
  active_issues: number;
  over_30_days: number;
  closed_since_review: number;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface DashboardIssueChartSlice {
  label: string;
  value: number;
}

export interface DashboardIssuesCharts {
  status: DashboardIssueChartSlice[];
  priority: DashboardIssueChartSlice[];
  discipline: DashboardIssueChartSlice[];
  zone: DashboardIssueChartSlice[];
  trend_90d: Array<{
    date: string | null;
    open: number;
    closed: number;
    total: number;
  }>;
  trend_90d_weekly: Array<{
    date: string | null;
    open: number;
    closed: number;
    total: number;
  }>;
  trend_all_time_monthly: Array<{
    date: string | null;
    open: number;
    closed: number;
    total: number;
  }>;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface DashboardIssuesTableRow {
  issue_id: string;
  source: string | null;
  project_name: string | null;
  status: string | null;
  priority: string | null;
  clash_level: string | null;
  title: string | null;
  latest_comment: string | null;
  company: string | null;
  zone: string | null;
  location_root: string | null;
  location_building: string | null;
  location_level: string | null;
  created_at: string | null;
}

export interface DashboardIssuesTable {
  page: number;
  page_size: number;
  total_count: number;
  rows: DashboardIssuesTableRow[];
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface CoordinateAlignmentControlPointRow {
  pm_project_id: number | null;
  project_name: string | null;
  control_file_name: string | null;
  control_zone_code: string | null;
  control_is_primary: boolean | null;
  control_pbp_eastwest?: number | null;
  control_pbp_northsouth?: number | null;
  control_pbp_elevation?: number | null;
  control_pbp_angle_true_north?: number | null;
  control_survey_eastwest?: number | null;
  control_survey_northsouth?: number | null;
  control_survey_elevation?: number | null;
  control_survey_angle_true_north?: number | null;
}

export interface CoordinateAlignmentModelPointRow {
  pm_project_id: number | null;
  project_name: string | null;
  model_file_name: string | null;
  discipline: string | null;
  model_zone_code: string | null;
  control_file_name: string | null;
  control_zone_code: string | null;
  control_is_primary: boolean | null;
  pbp_eastwest?: number | null;
  pbp_northsouth?: number | null;
  pbp_elevation?: number | null;
  pbp_angle_true_north?: number | null;
  pbp_compliant?: boolean | null;
  pbp_compliance_status?: string | null;
  survey_eastwest?: number | null;
  survey_northsouth?: number | null;
  survey_elevation?: number | null;
  survey_angle_true_north?: number | null;
  survey_compliant?: boolean | null;
  survey_compliance_status?: string | null;
}

export interface CoordinateAlignmentDashboard {
  control_base_points: CoordinateAlignmentControlPointRow[];
  control_survey_points: CoordinateAlignmentControlPointRow[];
  model_base_points: CoordinateAlignmentModelPointRow[];
  model_survey_points: CoordinateAlignmentModelPointRow[];
  total: number;
  page: number;
  page_size: number;
  error?: string;
  filters?: DashboardFilters;
  as_of?: string | null;
}

export interface GridAlignmentRow {
  pm_project_id: number | null;
  project_name: string | null;
  source_project_name: string | null;
  model_file_name: string | null;
  control_file_name: string | null;
  grid_name: string | null;
  discipline_full_name: string | null;
  model_exported_date: string | null;
  control_exported_date: string | null;
  angle_degrees: number | null;
  alignment_status: string | null;
  status_flag: string | null;
  description: string | null;
}

export interface GridAlignmentDashboard {
  items: GridAlignmentRow[];
  total: number;
  page: number;
  page_size: number;
  as_of?: string | null;
  filters?: DashboardFilters;
  error?: string;
}

export interface LevelAlignmentRow {
  pm_project_id: number | null;
  project_name: string | null;
  source_project_name: string | null;
  discipline_full_name: string | null;
  model_file_name: string | null;
  control_file_name: string | null;
  model_level_name: string | null;
  model_elevation_mm: number | null;
  control_level_name: string | null;
  control_elevation_mm: number | null;
  elevation_diff_mm: number | null;
  alignment_status: string | null;
  alignment_note: string | null;
}

export interface LevelAlignmentDashboard {
  items: LevelAlignmentRow[];
  total: number;
  page: number;
  page_size: number;
  tolerance_mm: number;
  as_of?: string | null;
  filters?: DashboardFilters;
  error?: string;
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

export interface ProjectReviewItem {
  review_id: number;
  service_id: number;
  project_id: number;
  cycle_no: number;
  planned_date?: string | null;
  due_date?: string | null;
  status?: string | null;
  disciplines?: string | null;
  deliverables?: string | null;
  is_billed?: boolean | null;
  billing_amount?: number | null;
  invoice_reference?: string | null;
  service_name?: string | null;
  service_code?: string | null;
  phase?: string | null;
}

export interface ProjectReviewsResponse {
  items: ProjectReviewItem[];
  total: number;
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
  invoice_reference?: string;
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

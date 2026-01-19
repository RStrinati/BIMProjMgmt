// API functions for service templates, project services, and service reviews

import apiClient from './client';
import type {
  ServiceItem,
  FileServiceTemplate,
  FileServiceTemplatePayload,
  ApplyTemplateResult,
  ServiceReview,
  ReviewBillingResponse,
  ServiceTemplateCatalogResponse,
  GeneratedServiceStructure,
  ServiceTemplateResyncResult,
} from '@/types/api';

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
  assigned_user_id?: number | null;
  assigned_user_name?: string | null;
}

export type ProjectServicesListResponse =
  | ProjectService[]
  | {
      items?: ProjectService[];
      services?: ProjectService[];
      results?: ProjectService[];
      total?: number;
      total_count?: number;
      count?: number;
      page?: number;
      page_size?: number;
      limit?: number;
      aggregate?: Record<string, unknown>;
      summary?: Record<string, unknown>;
      meta?: Record<string, unknown>;
    };

// Service Templates API
export const serviceTemplatesApi = {
  getAll: () => apiClient.get<ServiceTemplate[]>('/service_templates'),

  create: (data: {
    template_name: string;
    service_type: string;
    parameters: any;
    created_by: number;
    description?: string;
  }) => apiClient.post<{ success: boolean }>('/service_templates', data),

  update: (id: number, data: Partial<ServiceTemplate>) =>
    apiClient.patch<{ success: boolean }>(`/service_templates/${id}`, data),

  delete: (id: number) =>
    apiClient.delete<{ success: boolean }>(`/service_templates/${id}`),
};

export const serviceTemplateCatalogApi = {
  getAll: () => apiClient.get<ServiceTemplateCatalogResponse>('/service-templates'),
};

export const fileServiceTemplatesApi = {
  getAll: () => apiClient.get<FileServiceTemplate[]>('/service_templates/file'),
  save: (data: {
    template: FileServiceTemplatePayload;
    overwrite?: boolean;
    original_name?: string;
    force?: boolean;
  }) => apiClient.post<FileServiceTemplate>('/service_templates/file', data),
  delete: (name: string) =>
    apiClient.delete<{ deleted: string }>('/service_templates/file', {
      data: { name },
    }),
};

// Project Services API
export const projectServicesApi = {
  getAll: (projectId: number, params?: { page?: number; limit?: number }) =>
    apiClient
      .get<ProjectServicesListResponse>(`/projects/${projectId}/services`, { params })
      .then((response) => response.data),

  applyTemplate: (
    projectId: number,
    data: {
      template_name: string;
      replace_existing?: boolean;
      skip_duplicates?: boolean;
      overrides?: Record<string, unknown>;
    },
  ) => apiClient.post<ApplyTemplateResult>(`/projects/${projectId}/services/apply-template`, data),

  create: (projectId: number, data: {
    service_code: string;
    service_name: string;
    phase?: string;
    unit_type?: string;
    unit_qty?: number;
    unit_rate?: number;
    lump_sum_fee?: number;
    agreed_fee?: number;
    bill_rule?: string;
    notes?: string;
    assigned_user_id?: number | null;
  }) => apiClient.post<{ service_id: number }>(`/projects/${projectId}/services`, data),

  update: (projectId: number, serviceId: number, data: Partial<ProjectService>) =>
    apiClient.patch<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}`, data),

  delete: (projectId: number, serviceId: number) =>
    apiClient.delete<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}`),

  createFromTemplate: (
    projectId: number,
    data: {
      template_id: string;
      options_enabled?: string[];
      overrides?: {
        service_code?: string;
        service_name?: string;
        phase?: string;
        assigned_user_id?: number | null;
        agreed_fee?: number;
        unit_type?: string;
        unit_qty?: number;
        unit_rate?: number;
        lump_sum_fee?: number;
        bill_rule?: string;
        notes?: string;
      };
    },
  ) => apiClient.post(`/projects/${projectId}/services/from-template`, data),

  applyTemplateToService: (
    projectId: number,
    serviceId: number,
    data: {
      template_id: string;
      options_enabled?: string[];
      overrides?: Record<string, unknown>;
      dry_run?: boolean;
      mode?: 'sync_missing_only' | 'sync_and_update_managed';
    },
  ) => apiClient.post<ServiceTemplateResyncResult>(`/projects/${projectId}/services/${serviceId}/apply-template`, data),

  getGeneratedStructure: (projectId: number, serviceId: number) =>
    apiClient
      .get<GeneratedServiceStructure>(`/projects/${projectId}/services/${serviceId}/generated-structure`)
      .then((response) => response.data),
};

// Service Reviews API
export const serviceReviewsApi = {
  getAll: (projectId: number, serviceId: number) =>
    apiClient.get<ServiceReview[]>(`/projects/${projectId}/services/${serviceId}/reviews`),

  create: (projectId: number, serviceId: number, data: {
    cycle_no: number;
    planned_date: string;
    due_date?: string;
    disciplines?: string;
    deliverables?: string;
    status?: string;
    weight_factor?: number;
    invoice_reference?: string;
    evidence_links?: string;
    source_phase?: string;
    billing_phase?: string;
    billing_rate?: number;
    billing_amount?: number;
    is_billed?: boolean;
    origin?: string;
    is_template_managed?: boolean;
    sort_order?: number;
  }) => apiClient.post<{ review_id: number }>(`/projects/${projectId}/services/${serviceId}/reviews`, data),

  update: (projectId: number, serviceId: number, reviewId: number, data: Partial<ServiceReview>) =>
    apiClient.patch<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/reviews/${reviewId}`, data),

  delete: (projectId: number, serviceId: number, reviewId: number) =>
    apiClient.delete<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/reviews/${reviewId}`),

  getBillingSummary: (
    projectId: number,
    params?: { start_date?: string; end_date?: string; date_field?: 'actual_issued_at' | 'planned_date' | 'due_date' },
  ) =>
    apiClient
      .get<ReviewBillingResponse>(`/projects/${projectId}/review-billing`, { params })
      .then((response) => response.data),
};

// Service Items API
export const serviceItemsApi = {
  getAll: (projectId: number, serviceId: number, type?: string) =>
    apiClient.get<ServiceItem[]>(`/projects/${projectId}/services/${serviceId}/items${type ? `?type=${type}` : ''}`),

  create: (projectId: number, serviceId: number, data: {
    item_type: string;
    title: string;
    description?: string;
    planned_date?: string;
    due_date?: string;
    actual_date?: string;
    status?: string;
    priority?: string;
    assigned_to?: string;
    invoice_reference?: string;
    evidence_links?: string;
    notes?: string;
    is_billed?: boolean;
    project_id?: number;
    generated_from_template_id?: string;
    generated_from_template_version?: string;
    generated_key?: string;
    origin?: string;
    is_template_managed?: boolean;
    sort_order?: number;
  }) => apiClient.post<{ item_id: number }>(`/projects/${projectId}/services/${serviceId}/items`, data),

  update: (projectId: number, serviceId: number, itemId: number, data: Partial<ServiceItem>) =>
    apiClient.patch<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/items/${itemId}`, data),

  delete: (projectId: number, serviceId: number, itemId: number) =>
    apiClient.delete<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/items/${itemId}`),
};

// Service Items Statistics API
export const serviceItemsStatsApi = {
  getAll: (serviceId?: number) =>
    apiClient.get<Record<string, any>>(`/service_items_statistics${serviceId ? `?service_id=${serviceId}` : ''}`),
};

// Re-export types for component usage
export type { ServiceReview, ServiceItem };

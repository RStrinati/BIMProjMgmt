// API functions for service templates, project services, and service reviews

import apiClient from './client';
import type { ServiceItem } from '@/types/api';

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
  weight_factor: number;
  evidence_links?: string;
  actual_issued_at?: string;
}

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

// Project Services API
export const projectServicesApi = {
  getAll: (projectId: number) =>
    apiClient.get<ProjectService[]>(`/projects/${projectId}/services`),

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
  }) => apiClient.post<{ service_id: number }>(`/projects/${projectId}/services`, data),

  update: (projectId: number, serviceId: number, data: Partial<ProjectService>) =>
    apiClient.patch<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}`, data),

  delete: (projectId: number, serviceId: number) =>
    apiClient.delete<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}`),
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
    evidence_links?: string;
  }) => apiClient.post<{ review_id: number }>(`/projects/${projectId}/services/${serviceId}/reviews`, data),

  update: (projectId: number, serviceId: number, reviewId: number, data: Partial<ServiceReview>) =>
    apiClient.patch<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/reviews/${reviewId}`, data),

  delete: (projectId: number, serviceId: number, reviewId: number) =>
    apiClient.delete<{ success: boolean }>(`/projects/${projectId}/services/${serviceId}/reviews/${reviewId}`),
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
    evidence_links?: string;
    notes?: string;
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
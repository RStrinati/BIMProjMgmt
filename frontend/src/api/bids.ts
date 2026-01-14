import apiClient from './client';
import type {
  Bid,
  BidSection,
  BidScopeItem,
  BidScopeTemplate,
  BidProgramStage,
  BidBillingLine,
  BidAwardResult,
  BidVariation,
  SchemaHealthReport,
} from '@/types/api';

export const bidsApi = {
  list: async (params?: { status?: string; project_id?: number; client_id?: number }): Promise<Bid[]> => {
    const response = await apiClient.get<Bid[]>('/bids', { params });
    return response.data;
  },

  get: async (bidId: number): Promise<Bid> => {
    const response = await apiClient.get<Bid>(`/bids/${bidId}`);
    return response.data;
  },

  create: async (payload: Partial<Bid>): Promise<Bid> => {
    const response = await apiClient.post<Bid>('/bids', payload);
    return response.data;
  },

  update: async (bidId: number, payload: Partial<Bid>): Promise<Bid> => {
    const response = await apiClient.put<Bid>(`/bids/${bidId}`, payload);
    return response.data;
  },

  archive: async (bidId: number): Promise<void> => {
    await apiClient.delete(`/bids/${bidId}`);
  },

  getSections: async (bidId: number): Promise<BidSection[]> => {
    const response = await apiClient.get<BidSection[]>(`/bids/${bidId}/sections`);
    return response.data;
  },

  updateSections: async (bidId: number, sections: BidSection[]): Promise<void> => {
    await apiClient.put(`/bids/${bidId}/sections`, { sections });
  },

  listScopeItems: async (bidId: number): Promise<BidScopeItem[]> => {
    const response = await apiClient.get<BidScopeItem[]>(`/bids/${bidId}/scope-items`);
    return response.data;
  },

  createScopeItem: async (bidId: number, payload: Partial<BidScopeItem>): Promise<{ scope_item_id: number }> => {
    const response = await apiClient.post<{ scope_item_id: number }>(
      `/bids/${bidId}/scope-items`,
      payload,
    );
    return response.data;
  },

  updateScopeItem: async (bidId: number, scopeItemId: number, payload: Partial<BidScopeItem>): Promise<void> => {
    await apiClient.put(`/bids/${bidId}/scope-items/${scopeItemId}`, payload);
  },

  deleteScopeItem: async (bidId: number, scopeItemId: number): Promise<void> => {
    await apiClient.delete(`/bids/${bidId}/scope-items/${scopeItemId}`);
  },

  getScopeTemplates: async (): Promise<BidScopeTemplate[]> => {
    const response = await apiClient.get<BidScopeTemplate[]>('/bid_scope_templates');
    return response.data;
  },

  importScopeTemplate: async (
    bidId: number,
    payload: { template_name: string; replace_existing?: boolean },
  ): Promise<{ template_name: string; created_count: number; scope_item_ids: number[] }> => {
    const response = await apiClient.post<{ template_name: string; created_count: number; scope_item_ids: number[] }>(
      `/bids/${bidId}/scope-items/import-template`,
      payload,
    );
    return response.data;
  },

  listProgramStages: async (bidId: number): Promise<BidProgramStage[]> => {
    const response = await apiClient.get<BidProgramStage[]>(`/bids/${bidId}/program-stages`);
    return response.data;
  },

  createProgramStage: async (
    bidId: number,
    payload: Partial<BidProgramStage>,
  ): Promise<{ program_stage_id: number }> => {
    const response = await apiClient.post<{ program_stage_id: number }>(
      `/bids/${bidId}/program-stages`,
      payload,
    );
    return response.data;
  },

  updateProgramStage: async (
    bidId: number,
    programStageId: number,
    payload: Partial<BidProgramStage>,
  ): Promise<void> => {
    await apiClient.put(`/bids/${bidId}/program-stages/${programStageId}`, payload);
  },

  deleteProgramStage: async (bidId: number, programStageId: number): Promise<void> => {
    await apiClient.delete(`/bids/${bidId}/program-stages/${programStageId}`);
  },

  listBillingSchedule: async (bidId: number): Promise<BidBillingLine[]> => {
    const response = await apiClient.get<BidBillingLine[]>(`/bids/${bidId}/billing-schedule`);
    return response.data;
  },

  createBillingLine: async (
    bidId: number,
    payload: Partial<BidBillingLine>,
  ): Promise<{ billing_line_id: number }> => {
    const response = await apiClient.post<{ billing_line_id: number }>(
      `/bids/${bidId}/billing-schedule`,
      payload,
    );
    return response.data;
  },

  updateBillingLine: async (
    bidId: number,
    billingLineId: number,
    payload: Partial<BidBillingLine>,
  ): Promise<void> => {
    await apiClient.put(`/bids/${bidId}/billing-schedule/${billingLineId}`, payload);
  },

  deleteBillingLine: async (bidId: number, billingLineId: number): Promise<void> => {
    await apiClient.delete(`/bids/${bidId}/billing-schedule/${billingLineId}`);
  },

  award: async (
    bidId: number,
    payload: { create_new_project: boolean; project_id?: number; project_payload?: Record<string, any> },
  ): Promise<BidAwardResult> => {
    const response = await apiClient.post<BidAwardResult>(`/bids/${bidId}/award`, payload);
    return response.data;
  },

  listVariations: async (params?: { project_id?: number; bid_id?: number }): Promise<BidVariation[]> => {
    const response = await apiClient.get<BidVariation[]>('/variations', { params });
    return response.data;
  },

  createVariation: async (payload: Partial<BidVariation>): Promise<{ variation_id: number }> => {
    const response = await apiClient.post<{ variation_id: number }>('/variations', payload);
    return response.data;
  },

  getSchemaHealth: async (): Promise<SchemaHealthReport> => {
    const response = await apiClient.get<SchemaHealthReport>('/health/schema');
    return response.data;
  },
};

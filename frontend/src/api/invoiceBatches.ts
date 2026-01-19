import apiClient from './client';
import type { InvoiceBatch } from '@/types/api';

export const invoiceBatchesApi = {
  getAll: async (projectId: number, params?: { month?: string; service_id?: number }): Promise<InvoiceBatch[]> => {
    const response = await apiClient.get<InvoiceBatch[]>('/invoice_batches', {
      params: {
        project_id: projectId,
        month: params?.month,
        service_id: params?.service_id,
      },
    });
    return response.data;
  },

  create: async (data: {
    project_id: number;
    service_id?: number | null;
    invoice_month: string;
    status?: string;
    title?: string | null;
    notes?: string | null;
  }): Promise<{ invoice_batch_id: number }> => {
    const response = await apiClient.post<{ invoice_batch_id: number }>('/invoice_batches', data);
    return response.data;
  },

  update: async (invoiceBatchId: number, data: {
    status?: string;
    title?: string | null;
    notes?: string | null;
    invoice_month?: string;
    service_id?: number | null;
  }): Promise<{ success: boolean }> => {
    const response = await apiClient.patch<{ success: boolean }>(`/invoice_batches/${invoiceBatchId}`, data);
    return response.data;
  },
};

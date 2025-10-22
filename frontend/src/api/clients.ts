import apiClient from './client';
import type { Client } from '@/types/api';

export interface NamingConvention {
  code: string;
  name: string;
  standard: string;
  field_count: number;
}

export type { Client };
const normalizeClientPayload = (client: Partial<Client>) => {
  const {
    id,
    client_id,
    name,
    client_name,
    ...rest
  } = client;

  return {
    client_name: client_name ?? name,
    ...rest,
  };
};

export const clientsApi = {
  // Get all clients
  getAll: async (): Promise<Client[]> => {
    const response = await apiClient.get<Client[]>('/clients');
    return response.data;
  },

  // Get single client by ID
  getById: async (id: number): Promise<Client> => {
    const response = await apiClient.get<Client>(`/clients/${id}`);
    return response.data;
  },

  // Create new client
  create: async (client: Partial<Client>): Promise<Client> => {
    const response = await apiClient.post<Client>('/clients', normalizeClientPayload(client));
    return response.data;
  },

  // Update client
  update: async (id: number, client: Partial<Client>): Promise<Client> => {
    const response = await apiClient.put<Client>(`/clients/${id}`, normalizeClientPayload(client));
    return response.data;
  },

  // Delete client
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`/clients/${id}`);
  },
};

export const namingConventionsApi = {
  // Get all available naming conventions
  getAll: async (): Promise<NamingConvention[]> => {
    const response = await apiClient.get<NamingConvention[]>('/naming-conventions');
    return response.data;
  },
};

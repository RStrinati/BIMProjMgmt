import apiClient from './client';
import type { Task, TaskFilters, TaskPayload } from '@/types/api';

export interface TaskNotesViewResult {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
  raw: unknown;
}

const pickNumber = (...candidates: Array<unknown>): number | undefined => {
  for (const candidate of candidates) {
    const numeric = typeof candidate === 'number' ? candidate : Number(candidate);
    if (Number.isFinite(numeric)) {
      return numeric;
    }
  }
  return undefined;
};

const unwrapData = (input: unknown): unknown => {
  let current = input;
  let depth = 0;
  while (
    current &&
    typeof current === 'object' &&
    'data' in (current as Record<string, unknown>) &&
    depth < 3
  ) {
    const next = (current as Record<string, unknown>).data;
    if (next === current) {
      break;
    }
    current = next;
    depth += 1;
  }
  return current;
};

const normaliseTaskNotesResponse = (
  payload: unknown,
  request?: { page?: number; limit?: number },
): TaskNotesViewResult => {
  const base = unwrapData(payload);

  const candidateArrays: Array<Task[] | null> = [
    Array.isArray(base) ? (base as Task[]) : null,
    Array.isArray((base as any)?.tasks) ? ((base as any)?.tasks as Task[]) : null,
    Array.isArray((base as any)?.items) ? ((base as any)?.items as Task[]) : null,
    Array.isArray((base as any)?.results) ? ((base as any)?.results as Task[]) : null,
  ];

  const resolvedTasks = candidateArrays.find((value): value is Task[] => Array.isArray(value)) ?? [];

  const total =
    pickNumber(
      (base as any)?.total,
      (base as any)?.total_count,
      (base as any)?.count,
      (base as any)?.meta?.total,
      resolvedTasks.length,
    ) ?? resolvedTasks.length;

  const page =
    pickNumber((base as any)?.page, (base as any)?.current_page, (base as any)?.meta?.page) ??
    request?.page ??
    1;

  const pageSize =
    pickNumber(
      (base as any)?.page_size,
      (base as any)?.limit,
      (base as any)?.meta?.page_size,
      request?.limit,
      resolvedTasks.length || 1,
    ) ?? resolvedTasks.length;

  return {
    tasks: resolvedTasks,
    total: total < 0 ? resolvedTasks.length : total,
    page: page > 0 ? page : 1,
    pageSize: pageSize > 0 ? pageSize : resolvedTasks.length || 1,
    raw: payload,
  };
};

export const tasksApi = {
  getAll: async (filters?: TaskFilters): Promise<Task[]> => {
    const response = await apiClient.get<Task[]>('/tasks', { params: filters });
    return response.data;
  },

  getNotesView: async (
    filters?: TaskFilters & { page?: number; limit?: number },
  ): Promise<TaskNotesViewResult> => {
    const response = await apiClient.get('/tasks/notes-view', { params: filters });
    return normaliseTaskNotesResponse(response.data, filters);
  },

  create: async (task: TaskPayload): Promise<Task> => {
    const response = await apiClient.post<Task>('/tasks', task);
    return response.data;
  },

  update: async (id: number, task: Partial<TaskPayload>): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${id}`, task);
    return response.data;
  },

  delete: async (id: number, options?: { hardDelete?: boolean }): Promise<void> => {
    const params = options?.hardDelete ? { hard: 'true' } : undefined;
    await apiClient.delete(`/tasks/${id}`, { params });
  },

  toggleItem: async (taskId: number, itemIndex: number): Promise<Task> => {
    const response = await apiClient.put<Task>(`/tasks/${taskId}/items/${itemIndex}/toggle`);
    return response.data;
  },
};


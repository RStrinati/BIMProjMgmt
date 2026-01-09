/**
 * Dynamo Batch Automation API
 */

import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || '/api';

export interface DynamoScript {
  script_id: number;
  script_name: string;
  script_path: string;
  description?: string;
  category?: string;
  output_folder?: string;
  is_active: boolean;
  created_date: string;
  modified_date: string;
}

export interface DynamoBatchJob {
  job_id: number;
  job_name: string;
  script_id: number;
  project_id?: number;
  created_by?: number;
  status: 'pending' | 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_date: string;
  start_time?: string;
  end_time?: string;
  total_files: number;
  processed_files: number;
  success_count: number;
  error_count: number;
  task_file_path?: string;
  output_folder?: string;
  log_file_path?: string;
  error_message?: string;
  configuration?: string;
  script_name?: string;
  category?: string;
  file_status_breakdown?: Record<string, number>;
}

export interface RevitFile {
  file_name: string;
  file_path: string;
  relative_path: string;
  file_size_mb: number;
  modified_date?: string;
}

export interface JobConfiguration {
  detach_from_central?: boolean;
  audit_on_opening?: boolean;
  close_all_worksets?: boolean;
  discard_worksets?: boolean;
  timeout_minutes?: number;
}

export interface CreateJobRequest {
  job_name: string;
  script_id: number;
  file_paths: string[];
  project_id?: number;
  created_by?: number;
  configuration?: JobConfiguration;
}

export interface ImportScriptsRequest {
  folder_path: string;
  recursive?: boolean;
  category?: string;
  output_folder?: string;
}

export interface ImportScriptsResult {
  success: boolean;
  folder_path?: string;
  count?: number;
  scripts?: DynamoScript[];
  error?: string;
}

export interface ImportScriptsFilesRequest {
  file_paths: string[];
  category?: string;
  output_folder?: string;
}

export const dynamoBatchApi = {
  /**
   * Get available Dynamo scripts
   */
  getScripts: async (category?: string, activeOnly = true): Promise<DynamoScript[]> => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    params.append('active_only', String(activeOnly));
    
    const response = await axios.get<{ scripts: DynamoScript[] }>(
      `${API_BASE_URL}/dynamo/scripts?${params}`
    );
    return response.data.scripts;
  },

  /**
   * Get batch jobs
   */
  getJobs: async (
    projectId?: number,
    status?: string,
    limit = 50,
    offset = 0
  ): Promise<DynamoBatchJob[]> => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', String(projectId));
    if (status) params.append('status', status);
    params.append('limit', String(limit));
    params.append('offset', String(offset));
    
    const response = await axios.get<{ jobs: DynamoBatchJob[] }>(
      `${API_BASE_URL}/dynamo/jobs?${params}`
    );
    return response.data.jobs;
  },

  /**
   * Get detailed job status
   */
  getJobStatus: async (jobId: number): Promise<DynamoBatchJob> => {
    const response = await axios.get<{ job: DynamoBatchJob }>(
      `${API_BASE_URL}/dynamo/jobs/${jobId}`
    );
    return response.data.job;
  },

  /**
   * Create a new batch job
   */
  createJob: async (request: CreateJobRequest): Promise<number> => {
    const response = await axios.post<{ job_id: number }>(
      `${API_BASE_URL}/dynamo/jobs`,
      request
    );
    return response.data.job_id;
  },

  /**
   * Execute a batch job
   */
  executeJob: async (jobId: number): Promise<string> => {
    const response = await axios.post<{ message: string }>(
      `${API_BASE_URL}/dynamo/jobs/${jobId}/execute`
    );
    return response.data.message;
  },

  /**
   * Get Revit files for a project
   */
  getProjectRevitFiles: async (projectId: number): Promise<RevitFile[]> => {
    const response = await axios.get<{ files: RevitFile[] }>(
      `${API_BASE_URL}/projects/${projectId}/revit-files`
    );
    return response.data.files;
  },

  /**
   * Register Dynamo scripts from a folder
   */
  importScriptsFromFolder: async (request: ImportScriptsRequest): Promise<ImportScriptsResult> => {
    const response = await axios.post<ImportScriptsResult>(
      `${API_BASE_URL}/dynamo/scripts/import-folder`,
      request
    );
    return response.data;
  },

  /**
   * Register Dynamo scripts from file paths
   */
  importScriptsFromFiles: async (request: ImportScriptsFilesRequest): Promise<ImportScriptsResult> => {
    const response = await axios.post<ImportScriptsResult>(
      `${API_BASE_URL}/dynamo/scripts/import-files`,
      request
    );
    return response.data;
  },
};

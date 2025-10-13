/**
 * API client for Data Imports endpoints
 * Backend endpoints implemented in backend/app.py lines 855-1300
 */

import apiClient from './client';
import type {
  ACCImportLog,
  ACCImportRequest,
  ACCImportResponse,
  ACCConnectorFolder,
  ACCConnectorFilesResponse,
  ExtractACCFilesRequest,
  ExtractACCFilesResponse,
  ACCIssue,
  ACCIssuesResponse,
  ACCIssuesStats,
  ACCIssuesFilters,
  ReviztoExtractionRun,
  ReviztoExtractionRunsResponse,
  StartReviztoExtractionRequest,
  StartReviztoExtractionResponse,
  RevitHealthFile,
  RevitHealthFilesResponse,
  RevitHealthSummary
} from '../types/dataImports';
// ============================================================================
// Revit Health API
// ============================================================================

export const revitHealthApi = {
  /**
   * Get Revit health files for a project (paginated)
   * GET /api/projects/:project_id/revit-health-files
   */
  getHealthFiles: async (
    projectId: number,
    page: number = 1,
    pageSize: number = 25
  ): Promise<RevitHealthFilesResponse> => {
    const response = await apiClient.get<RevitHealthFilesResponse>(
      `/projects/${projectId}/revit-health-files`,
      { params: { page, limit: pageSize } }
    );
    return response.data;
  },

  /**
   * Get Revit health summary for a project
   * GET /api/projects/:project_id/revit-health-summary
   */
  getSummary: async (projectId: number): Promise<RevitHealthSummary> => {
    const response = await apiClient.get<RevitHealthSummary>(
      `/projects/${projectId}/revit-health-summary`
    );
    return response.data;
  },
};
// ============================================================================
// Revizto Extraction API
// ============================================================================

export const reviztoApi = {
  /**
   * Get Revizto extraction runs for a project (paginated)
   * GET /api/projects/:project_id/revizto-extractions
   */
  getExtractionRuns: async (
    page: number = 1,
    pageSize: number = 25,
    projectId?: number
  ): Promise<ReviztoExtractionRunsResponse> => {
    // If projectId is provided, use project-scoped endpoint
    const url = projectId
      ? `/projects/${projectId}/revizto-extractions`
      : `/revizto-extractions`;
    const response = await apiClient.get<ReviztoExtractionRunsResponse>(url, {
      params: { page, limit: pageSize },
    });
    return response.data;
  },

  /**
   * Get last Revizto extraction run (global or project)
   * GET /api/projects/:project_id/revizto-extractions/last
   */
  getLastRun: async (projectId?: number): Promise<ReviztoExtractionRun> => {
    const url = projectId
      ? `/projects/${projectId}/revizto-extractions/last`
      : `/revizto-extractions/last`;
    const response = await apiClient.get<ReviztoExtractionRun>(url);
    return response.data;
  },

  /**
   * Start a new Revizto extraction run
   * POST /api/projects/:project_id/revizto-extract
   */
  startExtraction: async (
    request: StartReviztoExtractionRequest
  ): Promise<StartReviztoExtractionResponse> => {
    const projectId = request.project_id;
    const url = projectId
      ? `/projects/${projectId}/revizto-extract`
      : `/revizto-extract`;
    const response = await apiClient.post<StartReviztoExtractionResponse>(url, request);
    return response.data;
  },
};
// ============================================================================
// ACC Issues API
// ============================================================================

export const accIssuesApi = {
  /**
   * Get ACC issues for a project with filters and pagination
   * GET /api/projects/:project_id/acc-issues
   */
  getIssues: async (
    projectId: number,
    filters: ACCIssuesFilters = {},
    page: number = 1,
    pageSize: number = 25
  ): Promise<ACCIssuesResponse> => {
    const response = await apiClient.get<ACCIssuesResponse>(
      `/projects/${projectId}/acc-issues`,
      { params: { ...filters, page, limit: pageSize } }
    );
    return response.data;
  },

  /**
   * Get ACC issues statistics for a project
   * GET /api/projects/:project_id/acc-issues-stats
   */
  getStats: async (projectId: number): Promise<ACCIssuesStats> => {
    const response = await apiClient.get<ACCIssuesStats>(
      `/projects/${projectId}/acc-issues-stats`
    );
    return response.data;
  },
};

// ============================================================================
// ACC Data Import API - Simplified to match Tkinter workflow
// ============================================================================

export const accDataImportApi = {
  /**
   * Get import logs/history for a project
   * GET /api/projects/:project_id/acc-data-import-logs
   */
  getImportLogs: async (projectId: number): Promise<{ logs: ACCImportLog[] }> => {
    const response = await apiClient.get<{ logs: ACCImportLog[] }>(
      `/projects/${projectId}/acc-data-import-logs`
    );
    return response.data;
  },

  /**
   * Import ACC data for a project
   * POST /api/projects/:project_id/acc-data-import
   * Note: Backend expects { folder_path }, we map from { file_path } provided by UI
   */
  importData: async (
    projectId: number,
    request: Pick<ACCImportRequest, 'file_path' | 'import_type'>
  ): Promise<ACCImportResponse> => {
    const payload = { folder_path: request.file_path } as const;
    const response = await apiClient.post<ACCImportResponse>(
      `/projects/${projectId}/acc-data-import`,
      payload
    );
    return response.data;
  },
};

// ============================================================================
// ACC Desktop Connector API (compatibility for existing components)
// ============================================================================

export const accConnectorApi = {
  /** Get current ACC Desktop Connector folder for project */
  getFolder: async (projectId: number): Promise<ACCConnectorFolder> => {
    const res = await apiClient.get<ACCConnectorFolder>(
      `/projects/${projectId}/acc-connector-folder`
    );
    return res.data;
  },

  /** Save ACC Desktop Connector folder for project */
  saveFolder: async (projectId: number, folder_path: string): Promise<{ success: boolean; project_id: number; folder_path: string }> => {
    const res = await apiClient.post<{ success: boolean; project_id: number; folder_path: string }>(
      `/projects/${projectId}/acc-connector-folder`,
      { folder_path }
    );
    return res.data;
  },

  /** List extracted files */
  getFiles: async (
    projectId: number,
    page: number = 1,
    pageSize: number = 50
  ): Promise<ACCConnectorFilesResponse> => {
    const res = await apiClient.get<ACCConnectorFilesResponse>(
      `/projects/${projectId}/acc-connector-files`,
      { params: { page, limit: pageSize } }
    );
    return res.data;
  },

  /** Extract files from configured folder */
  extractFiles: async (
    projectId: number,
    request: ExtractACCFilesRequest
  ): Promise<ExtractACCFilesResponse> => {
    const res = await apiClient.post<ExtractACCFilesResponse>(
      `/projects/${projectId}/acc-connector-extract`,
      request
    );
    return res.data;
  },
};

// Backward-compat: some code imports dataImportsApi; provide alias with current group
export const dataImportsApi = {
  acc: accDataImportApi,
  connector: accConnectorApi,
  issues: accIssuesApi,
  revizto: reviztoApi,
  revitHealth: revitHealthApi,
};

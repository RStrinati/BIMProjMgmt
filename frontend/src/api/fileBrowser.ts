/**
 * File Browser and Application Launcher API
 * Provides file/folder selection and external application launching
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export interface FileSelectionResult {
  success: boolean;
  file_path?: string;
  file_name?: string;
  exists?: boolean;
  message?: string;
}

export interface FolderSelectionResult {
  success: boolean;
  folder_path?: string;
  folder_name?: string;
  exists?: boolean;
  message?: string;
}

export interface FileType {
  description: string;
  extensions: string[];
}

export interface SelectFileOptions {
  title?: string;
  file_types?: [string, string][]; // [description, pattern]
  initial_dir?: string;
}

export interface SelectFolderOptions {
  title?: string;
  initial_dir?: string;
}

export interface LaunchAppOptions {
  app_path: string;
  args?: string[];
  working_dir?: string;
}

export interface AppLaunchResult {
  success: boolean;
  app_path?: string;
  args?: string[];
  message?: string;
  error?: string;
  searched_paths?: string[];
}

export interface HealthImporterOptions {
  folder_path: string;
  project_id?: number;
}

export interface HealthImporterResult {
  success: boolean;
  folder_path?: string;
  project_id?: number;
  execution_time_seconds?: number;
  message?: string;
  error?: string;
}

/**
 * File Browser API
 */
export const fileBrowserApi = {
  /**
   * Open file selection dialog
   */
  selectFile: async (options?: SelectFileOptions): Promise<FileSelectionResult> => {
    const response = await axios.post<FileSelectionResult>(
      `${API_BASE_URL}/file-browser/select-file`,
      options || {}
    );
    return response.data;
  },

  /**
   * Open folder selection dialog
   */
  selectFolder: async (options?: SelectFolderOptions): Promise<FolderSelectionResult> => {
    const response = await axios.post<FolderSelectionResult>(
      `${API_BASE_URL}/file-browser/select-folder`,
      options || {}
    );
    return response.data;
  },
};

/**
 * Application Launcher API
 */
export const applicationApi = {
  /**
   * Launch an external application
   */
  launch: async (options: LaunchAppOptions): Promise<AppLaunchResult> => {
    const response = await axios.post<AppLaunchResult>(
      `${API_BASE_URL}/applications/launch`,
      options
    );
    return response.data;
  },

  /**
   * Launch Revizto Data Exporter
   */
  launchReviztoExporter: async (customPath?: string): Promise<AppLaunchResult> => {
    const response = await axios.post<AppLaunchResult>(
      `${API_BASE_URL}/applications/revizto-exporter`,
      customPath ? { app_path: customPath } : {}
    );
    return response.data;
  },
};

/**
 * Script Runner API
 */
export const scriptApi = {
  /**
   * Run Revit health check importer on a folder
   */
  runHealthImporter: async (options: HealthImporterOptions): Promise<HealthImporterResult> => {
    const response = await axios.post<HealthImporterResult>(
      `${API_BASE_URL}/scripts/run-health-importer`,
      options
    );
    return response.data;
  },
};

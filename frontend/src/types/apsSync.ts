export interface ApsHub {
  id: string;
  name: string;
  region?: string | null;
  projectsLink?: string;
}

export interface ApsProject {
  id: string;
  name: string;
  status?: string | null;
  created?: string | null;
  updated?: string | null;
  detailsLink?: string;
  usersLink?: string;
  issuesLink?: string;
  filesLink?: string;
}

export interface ApsHubsResponse {
  success?: boolean;
  hubCount?: number;
  authMethod?: string;
  userToken?: boolean;
  hubs?: ApsHub[];
  error?: string;
  message?: string;
  nextStep?: string;
  authRecommendation?: string;
  fallback_used?: boolean;
}

export interface ApsProjectsResponse {
  success?: boolean;
  hubId?: string;
  projectCount?: number;
  projects?: ApsProject[];
  error?: string;
  message?: string;
  nextSteps?: string[];
  fallback_used?: boolean;
}

export interface ApsLoginInfo {
  login_url: string;
  service_base: string;
  flow: string;
  note?: string;
}

// Project Details Types
export interface ApsProjectDetails {
  success: boolean;
  authMethod?: string;
  projectInfo: {
    id: string;
    name: string;
    status: string;
    created: string;
    updated: string;
    totalTopLevelFolders: number;
    totalFiles: number;
    modelFolders: ApsModelFolder[];
  };
  folders: ApsFolder[];
  actions?: {
    users?: string;
    issues?: string;
    files?: string;
  };
  fallback_used?: boolean;
  error?: string;
}

export interface ApsFolder {
  id: string;
  name: string;
  created: string;
  modified: string;
}

export interface ApsModelFolder {
  name: string;
  fileCount: number;
  lastModified: string;
}

// Files Types
export interface ApsProjectFiles {
  success: boolean;
  authMethod?: string;
  projectId: string;
  totalFiles: number;
  lastUpdated?: string | null;
  modelFiles: ApsModelFile[];
  allFiles: ApsFile[];
  folders: ApsFolderSummary[];
  fallback_used?: boolean;
  error?: string;
  navigation?: {
    overview?: string;
    issues?: string;
    users?: string;
  };
}

export interface ApsFile {
  id: string;
  name: string;
  extension?: string;
  size?: number;
  created: string;
  modified: string;
  version?: number;
  folder: string;
}

export interface ApsModelFile extends ApsFile {
  // Model files are files with CAD/BIM extensions
}

export interface ApsFolderSummary {
  id: string;
  name: string;
  counts?: {
    files: number;
    models: number;
  };
}

// Issues Types
export interface ApsProjectIssues {
  success: boolean;
  authMethod?: string;
  projectId: string;
  totalIssues?: number;
  issueCount?: number;
  issues: ApsIssue[];
  page?: number;
  limit?: number;
  fallback_used?: boolean;
  error?: string;
}

export interface ApsIssue {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority?: string;
  type?: string;
  assigned_to?: string;
  owner?: string;
  created: string;
  due_date?: string;
  closed_date?: string;
  location?: string;
  custom_attributes?: Record<string, any>;
}

// Users Types
export interface ApsProjectUsers {
  success: boolean;
  authMethod?: string;
  projectId: string;
  userCount: number;
  users: ApsUser[];
  fallback_used?: boolean;
  error?: string;
}

export interface ApsUser {
  id: string;
  name: string;
  email?: string;
  role?: string;
  status?: string;
  company?: string;
  lastSignIn?: string;
}

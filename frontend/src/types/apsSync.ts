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

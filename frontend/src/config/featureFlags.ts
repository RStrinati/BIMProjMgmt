const readEnvFlag = (key: string): boolean | undefined => {
  const raw = (import.meta.env[key] as string | undefined)?.trim();
  if (!raw) {
    return undefined;
  }
  if (['1', 'true', 'yes', 'on'].includes(raw.toLowerCase())) {
    return true;
  }
  if (['0', 'false', 'no', 'off'].includes(raw.toLowerCase())) {
    return false;
  }
  return undefined;
};

const readLocalFlag = (key: string): boolean | undefined => {
  if (typeof window === 'undefined') {
    return undefined;
  }
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return undefined;
  }
  if (raw === '1' || raw.toLowerCase() === 'true') {
    return true;
  }
  if (raw === '0' || raw.toLowerCase() === 'false') {
    return false;
  }
  return undefined;
};

// Create a Proxy-based feature flags object that evaluates flags at runtime
// This allows tests to set localStorage flags before the component renders
export const featureFlags = new Proxy({}, {
  get: (target, prop: string | symbol) => {
    if (typeof prop !== 'string') return undefined;
    
    switch (prop) {
      case 'projectsPanel':
        return readLocalFlag('ff_projects_panel') ?? readEnvFlag('VITE_FF_PROJECTS_PANEL') ?? false;
      case 'bidsPanel':
        return readLocalFlag('ff_bids_panel') ?? readEnvFlag('VITE_FF_BIDS_PANEL') ?? false;
      case 'projectWorkspaceV2':
        return readLocalFlag('ff_project_workspace_v2') ?? readEnvFlag('VITE_FF_PROJECT_WORKSPACE_V2') ?? false;
      case 'linearTimeline':
        return readLocalFlag('ff_linear_timeline') ?? readEnvFlag('VITE_FF_LINEAR_TIMELINE') ?? false;
      case 'projectsHomeV2':
        return readLocalFlag('ff_projects_home_v2') ?? readEnvFlag('VITE_FF_PROJECTS_HOME_V2') ?? false;
      case 'anchorLinks':
        return readLocalFlag('ff_anchor_links') ?? readEnvFlag('VITE_FF_ANCHOR_LINKS') ?? false;
      case 'issuesHub':
        return readLocalFlag('ff_issues_hub') ?? readEnvFlag('VITE_FF_ISSUES_HUB') ?? false;
      default:
        return undefined;
    }
  }
}) as Record<string, boolean>;


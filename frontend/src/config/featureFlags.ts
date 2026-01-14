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

export const featureFlags = {
  projectsPanel: readLocalFlag('ff_projects_panel') ?? readEnvFlag('VITE_FF_PROJECTS_PANEL') ?? false,
  bidsPanel: readLocalFlag('ff_bids_panel') ?? readEnvFlag('VITE_FF_BIDS_PANEL') ?? false,
  projectWorkspaceV2:
    readLocalFlag('ff_project_workspace_v2') ?? readEnvFlag('VITE_FF_PROJECT_WORKSPACE_V2') ?? false,
  linearTimeline:
    readLocalFlag('ff_linear_timeline') ?? readEnvFlag('VITE_FF_LINEAR_TIMELINE') ?? false,
};

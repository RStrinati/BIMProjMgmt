// Issues API functions
export const issuesApi = {
  // Get overall issues overview for all projects
  getOverview: async () => {
    const response = await fetch('/api/issues/overview');
    if (!response.ok) {
      throw new Error('Failed to fetch issues overview');
    }
    return response.json();
  },

  // Get issues overview for a specific project
  getProjectOverview: async (projectId: number) => {
    const response = await fetch(`/api/projects/${projectId}/issues/overview`);
    if (!response.ok) {
      throw new Error('Failed to fetch project issues overview');
    }
    return response.json();
  },
};
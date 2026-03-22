import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { useDashboardFilters } from './DashboardFiltersContext';

export function useDashboardProjectFilter() {
  const { filters } = useDashboardFilters();
  const { data: projects = [] } = useQuery({
    queryKey: ['dashboard', 'project-summary'],
    queryFn: () => projectsApi.getSummary({ viewId: 'all' }),
  });

  const filteredProjectIds = useMemo(() => {
    const normalizedManager = filters.manager.toLowerCase();
    const normalizedClient = filters.client.toLowerCase();
    const normalizedType = filters.projectType.toLowerCase();

    return projects
      .filter((project) => {
        const managerMatch =
          filters.manager === 'all' ||
          (project.project_manager ?? '').toLowerCase() === normalizedManager;
        const clientMatch =
          filters.client === 'all' || (project.client_name ?? '').toLowerCase() === normalizedClient;
        const typeMatch =
          filters.projectType === 'all' || (project.project_type ?? '').toLowerCase() === normalizedType;
        const explicitMatch =
          filters.projectIds.length === 0 || filters.projectIds.includes(project.project_id);
        return managerMatch && clientMatch && typeMatch && explicitMatch;
      })
      .map((project) => project.project_id);
  }, [projects, filters]);

  return { projectIds: filteredProjectIds, projects };
}

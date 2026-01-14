import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { Project } from '@/types/api';
import { projectsApi } from '@/api/projects';

type UpdateProjectArgs = {
  projectId: number;
  patch: Partial<Project>;
};

type UpdateProjectContext = {
  previousProject?: Project;
  previousProjectLists?: Array<[unknown, Project[]]>;
};

export function useUpdateProject() {
  const queryClient = useQueryClient();

  return useMutation<Project, Error, UpdateProjectArgs, UpdateProjectContext>({
    mutationFn: ({ projectId, patch }) => projectsApi.update(projectId, patch),
    onMutate: async ({ projectId, patch }) => {
      await queryClient.cancelQueries({ queryKey: ['project', projectId] });
      await queryClient.cancelQueries({ queryKey: ['projects'] });

      const previousProject = queryClient.getQueryData<Project>(['project', projectId]);
      const previousProjectLists = queryClient.getQueriesData<Project[]>({ queryKey: ['projects'] });

      if (previousProject) {
        queryClient.setQueryData<Project>(['project', projectId], {
          ...previousProject,
          ...patch,
        });
      }

      queryClient.setQueriesData<Project[]>(
        { queryKey: ['projects'] },
        (existing) =>
          existing
            ? existing.map((project) =>
                project.project_id === projectId ? { ...project, ...patch } : project,
              )
            : existing,
      );

      return { previousProject, previousProjectLists };
    },
    onError: (_err, { projectId }, context) => {
      if (context?.previousProject) {
        queryClient.setQueryData(['project', projectId], context.previousProject);
      }
      if (context?.previousProjectLists) {
        context.previousProjectLists.forEach(([key, data]) => {
          queryClient.setQueryData(key, data);
        });
      }
    },
    onSettled: (_data, _error, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

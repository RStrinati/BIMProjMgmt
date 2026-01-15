/**
 * React Query hooks for IssueAnchorLinks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { anchorLinksApi, AnchorLinkedIssuesResponse, AnchorBlockerCounts, CreateIssueLinkPayload } from '@/api/anchorLinksApi';

/**
 * Hook to fetch blocker counts for an anchor
 */
export function useAnchorCounts(
  projectId: number,
  anchorType: 'review' | 'service' | 'item',
  anchorId: number,
  enabled: boolean = true,
) {
  return useQuery<AnchorBlockerCounts>({
    queryKey: ['anchorCounts', projectId, anchorType, anchorId],
    queryFn: () => anchorLinksApi.getAnchorBlockerCounts(projectId, anchorType, anchorId),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
    enabled,
  });
}

/**
 * Hook to fetch paginated linked issues for an anchor
 */
export function useAnchorLinkedIssues(
  projectId: number,
  anchorType: 'review' | 'service' | 'item',
  anchorId: number,
  page: number = 1,
  pageSize: number = 20,
  sortBy: string = 'updated_at',
  sortDir: string = 'DESC',
  linkRole?: string,
  enabled: boolean = true,
) {
  return useQuery<AnchorLinkedIssuesResponse>({
    queryKey: ['anchorLinkedIssues', projectId, anchorType, anchorId, page, pageSize, sortBy, sortDir, linkRole],
    queryFn: () =>
      anchorLinksApi.getAnchorLinkedIssues(
        projectId,
        anchorType,
        anchorId,
        page,
        pageSize,
        sortBy,
        sortDir,
        linkRole,
      ),
    staleTime: 1000 * 60 * 5, // 5 minutes
    gcTime: 1000 * 60 * 10, // 10 minutes
    enabled,
  });
}

/**
 * Hook to create an issue-anchor link with optimistic update
 */
export function useCreateIssueLink() {
  const queryClient = useQueryClient();

  return useMutation(
    (payload: CreateIssueLinkPayload) => anchorLinksApi.createIssueLink(payload),
    {
      onMutate: async (payload) => {
        // Optimistic update: invalidate counts and issues queries
        await queryClient.cancelQueries({
          queryKey: ['anchorCounts', payload.project_id, payload.anchor_type, payload.anchor_id],
        });
        await queryClient.cancelQueries({
          queryKey: ['anchorLinkedIssues', payload.project_id, payload.anchor_type, payload.anchor_id],
        });

        // Return rollback data
        return {
          projectId: payload.project_id,
          anchorType: payload.anchor_type,
          anchorId: payload.anchor_id,
        };
      },
      onSuccess: (data, payload) => {
        // Invalidate queries to refresh data
        queryClient.invalidateQueries({
          queryKey: ['anchorCounts', payload.project_id, payload.anchor_type, payload.anchor_id],
        });
        queryClient.invalidateQueries({
          queryKey: ['anchorLinkedIssues', payload.project_id, payload.anchor_type, payload.anchor_id],
        });
      },
      onError: (error, payload, context) => {
        // Rollback on error (queries already cancelled and reverted above)
        console.error('Error creating issue link:', error);
      },
    }
  );
}

/**
 * Hook to delete (soft-delete) an issue-anchor link with optimistic update
 */
export function useDeleteIssueLink(projectId: number, anchorType: 'review' | 'service' | 'item', anchorId: number) {
  const queryClient = useQueryClient();

  return useMutation(
    (linkId: number) => anchorLinksApi.deleteIssueLink(linkId),
    {
      onMutate: async () => {
        // Optimistic update: invalidate queries
        await queryClient.cancelQueries({
          queryKey: ['anchorCounts', projectId, anchorType, anchorId],
        });
        await queryClient.cancelQueries({
          queryKey: ['anchorLinkedIssues', projectId, anchorType, anchorId],
        });
      },
      onSuccess: () => {
        // Refresh data
        queryClient.invalidateQueries({
          queryKey: ['anchorCounts', projectId, anchorType, anchorId],
        });
        queryClient.invalidateQueries({
          queryKey: ['anchorLinkedIssues', projectId, anchorType, anchorId],
        });
      },
      onError: (error) => {
        console.error('Error deleting issue link:', error);
      },
    }
  );
}

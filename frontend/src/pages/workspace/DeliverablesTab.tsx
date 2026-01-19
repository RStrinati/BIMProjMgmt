/**
 * Deliverables Tab
 * 
 * Displays project reviews (deliverables).
 * Reuses existing deliverables UI from ProjectWorkspacePageV2.
 */

import { useMemo, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Typography,
} from '@mui/material';
import { serviceReviewsApi } from '@/api';
import type { Project, ProjectReviewItem, ProjectReviewsResponse, ServiceReview } from '@/types/api';
import { useProjectReviews } from '@/hooks/useProjectReviews';
import { toApiReviewStatus } from '@/utils/reviewStatus';
import { EditableCell, ToggleCell } from '@/components/projects/EditableCells';
import { LinearListContainer, LinearListHeaderRow, LinearListRow, LinearListCell } from '@/components/ui/LinearList';

type OutletContext = {
  projectId: number;
  project: Project | null;
};

const formatDate = (value?: string | null) => {
  if (!value) return '--';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

export default function DeliverablesTab() {
  const { projectId } = useOutletContext<OutletContext>();
  const queryClient = useQueryClient();
  const [reviewUpdateError, setReviewUpdateError] = useState<string | null>(null);

  const reviewsFilters = useMemo(
    () => ({
      sort_by: 'planned_date' as const,
      sort_dir: 'asc' as const,
    }),
    [],
  );

  const {
    data: projectReviews,
    isLoading: projectReviewsLoading,
    error: projectReviewsError,
  } = useProjectReviews(projectId, reviewsFilters);

  const reviewItems = useMemo<ProjectReviewItem[]>(
    () => projectReviews?.items ?? [],
    [projectReviews],
  );

  const updateDeliverableField = useMutation<
    ProjectReviewItem,
    Error,
    { review: ProjectReviewItem; fieldName: string; value: unknown },
    { previousProjectReviews: Array<[unknown, ProjectReviewsResponse | undefined]> }
  >({
    mutationFn: async ({ review, fieldName, value }) => {
      const payload = { [fieldName]: value };
      const { default: projectReviewsApi } = await import('@/api/projectReviews');
      return projectReviewsApi.patchProjectReview(projectId, review.review_id, review.service_id, payload as any);
    },
    onMutate: async ({ review, fieldName, value }) => {
      setReviewUpdateError(null);
      await queryClient.cancelQueries({ queryKey: ['projectReviews', projectId] });

      const previousProjectReviews = queryClient.getQueriesData<ProjectReviewsResponse>({
        queryKey: ['projectReviews', projectId],
      });

      queryClient.setQueriesData<ProjectReviewsResponse>(
        { queryKey: ['projectReviews', projectId] },
        (existing) => {
          if (!existing) return existing;
          return {
            ...existing,
            items: existing.items.map((item) =>
              item.review_id === review.review_id ? { ...item, [fieldName]: value } : item,
            ),
          };
        },
      );

      return { previousProjectReviews };
    },
    onError: (error, _variables, context) => {
      setReviewUpdateError(error.message || 'Failed to update review.');
      if (context?.previousProjectReviews) {
        context.previousProjectReviews.forEach(([key, data]) => {
          queryClient.setQueryData(key as unknown[], data);
        });
      }
    },
    onSettled: (_data, _error, { review }) => {
      queryClient.invalidateQueries({ queryKey: ['projectReviews', projectId] });
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, review.service_id] });
    },
  });

  return (
    <Box data-testid="workspace-deliverables-tab">
      {reviewUpdateError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {reviewUpdateError}
        </Alert>
      )}
      {projectReviewsError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load project reviews.
        </Alert>
      )}
      {projectReviewsLoading ? (
        <Typography color="text.secondary">Loading deliverables...</Typography>
      ) : reviewItems.length ? (
        <LinearListContainer>
          <LinearListHeaderRow columns={['Service', 'Planned', 'Due', 'Invoice #', 'Invoice Date', 'Billed']} />
          {reviewItems.map((review) => {
            const serviceLabel = [review.service_code, review.service_name]
              .filter(Boolean)
              .join(' | ');
            const metadataLabel = [review.phase, review.cycle_no ? `Cycle ${review.cycle_no}` : null]
              .filter(Boolean)
              .join(' | ');

            return (
              <LinearListRow
                key={review.review_id}
                testId={`deliverable-row-${review.review_id}`}
                columns={6}
                hoverable
              >
                {/* Service + metadata */}
                <Box>
                  <Typography variant="body2" fontWeight={500}>
                    {serviceLabel || 'Service'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {metadataLabel}
                  </Typography>
                </Box>

                {/* Planned Date (read-only) */}
                <LinearListCell variant="secondary">
                  {formatDate(review.planned_date)}
                </LinearListCell>

                {/* Due Date - Editable */}
                <EditableCell
                  value={review.due_date}
                  type="date"
                  testId={`cell-due-${review.review_id}`}
                  isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'due_date'}
                  onSave={async (newValue) => {
                    await updateDeliverableField.mutateAsync({
                      review,
                      fieldName: 'due_date',
                      value: newValue,
                    });
                  }}
                />

                {/* Invoice Number - Editable */}
                <EditableCell
                  value={review.invoice_reference}
                  type="text"
                  testId={`cell-invoice-number-${review.review_id}`}
                  isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_reference'}
                  onSave={async (newValue) => {
                    await updateDeliverableField.mutateAsync({
                      review,
                      fieldName: 'invoice_reference',
                      value: newValue,
                    });
                  }}
                />

                {/* Invoice Date - Editable */}
                <EditableCell
                  value={review.invoice_date}
                  type="date"
                  testId={`cell-invoice-date-${review.review_id}`}
                  isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'invoice_date'}
                  onSave={async (newValue) => {
                    await updateDeliverableField.mutateAsync({
                      review,
                      fieldName: 'invoice_date',
                      value: newValue,
                    });
                  }}
                />

                {/* Billing Status - Toggleable */}
                <ToggleCell
                  value={review.is_billed}
                  testId={`cell-billing-status-${review.review_id}`}
                  isSaving={updateDeliverableField.isPending && updateDeliverableField.variables?.review.review_id === review.review_id && updateDeliverableField.variables?.fieldName === 'is_billed'}
                  onSave={async (newValue) => {
                    await updateDeliverableField.mutateAsync({
                      review,
                      fieldName: 'is_billed',
                      value: newValue,
                    });
                  }}
                />
              </LinearListRow>
            );
          })}
        </LinearListContainer>
      ) : (
        <Typography color="text.secondary">No deliverables found for this project.</Typography>
      )}
    </Box>
  );
}

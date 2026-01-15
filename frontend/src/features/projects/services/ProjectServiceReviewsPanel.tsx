import { useEffect, useState } from 'react';
import { Alert, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { serviceReviewsApi } from '@/api/services';
import { ListView } from '@/components/ui/ListView';
import { InlineField } from '@/components/ui/InlineField';
import { ReviewStatusInline } from '@/components/projects/ReviewStatusInline';
import { useUpdateReviewStatus } from '@/hooks/useUpdateReviewStatus';
import type { ProjectService } from '@/api/services';
import type { ServiceReview } from '@/types/api';
import { formatReviewStatusLabel } from '@/utils/reviewStatus';

type ProjectServiceReviewsPanelProps = {
  projectId: number;
  service: ProjectService | null;
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '--';
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? String(value) : parsed.toLocaleDateString();
};

export function ProjectServiceReviewsPanel({ projectId, service }: ProjectServiceReviewsPanelProps) {
  const updateReviewStatus = useUpdateReviewStatus();
  const [reviewSaveError, setReviewSaveError] = useState<string | null>(null);
  const [selectedReviewId, setSelectedReviewId] = useState<number | null>(null);

  const {
    data: reviews = [],
    isLoading: reviewsLoading,
    isFetching: reviewsFetching,
  } = useQuery<ServiceReview[]>({
    queryKey: ['serviceReviews', projectId, service?.service_id],
    queryFn: async () => {
      if (!service) {
        return [];
      }
      const response = await serviceReviewsApi.getAll(projectId, service.service_id);
      return response.data;
    },
    enabled: Boolean(service),
  });

  useEffect(() => {
    if (!reviews.length) {
      setSelectedReviewId(null);
      return;
    }
    const stillExists = reviews.some((review) => review.review_id === selectedReviewId);
    if (!stillExists) {
      setSelectedReviewId(reviews[0].review_id);
    }
  }, [reviews, selectedReviewId]);

  const selectedReview =
    reviews.find((review) => review.review_id === selectedReviewId) ?? reviews[0] ?? null;

  const handleReviewStatusChange = (nextStatus: string | null) => {
    if (!service || !selectedReview) {
      return;
    }
    setReviewSaveError(null);
    updateReviewStatus.mutate(
      {
        projectId,
        serviceId: service.service_id,
        reviewId: selectedReview.review_id,
        status: nextStatus,
      },
      {
        onError: (error) => {
          setReviewSaveError(error.message || 'Failed to update review status.');
        },
      },
    );
  };

  return (
    <Stack spacing={2}>
      <Typography variant="subtitle2">Reviews</Typography>
      <ListView<ServiceReview>
        items={reviews}
        getItemId={(review) => review.review_id}
        getItemTestId={(review) => `projects-panel-review-row-${review.review_id}`}
        selectedId={selectedReview?.review_id ?? null}
        onSelect={(review) => setSelectedReviewId(review.review_id)}
        renderPrimary={(review) =>
          `Cycle ${review.cycle_no} · ${formatReviewStatusLabel(review.status)}`
        }
        renderSecondary={(review) =>
          [
            `Planned: ${formatDate(review.planned_date)}`,
            review.due_date ? `Due: ${formatDate(review.due_date)}` : null,
            review.disciplines ? `Disciplines: ${review.disciplines}` : null,
            review.deliverables ? `Deliverables: ${review.deliverables}` : null,
            review.is_billed != null ? `Billed: ${review.is_billed ? 'Yes' : 'No'}` : null,
          ]
            .filter(Boolean)
            .join(' | ')
        }
        emptyState={
          <Typography color="text.secondary" sx={{ px: 2 }}>
            {reviewsLoading || reviewsFetching
              ? 'Loading reviews...'
              : 'No reviews for this service yet.'}
          </Typography>
        }
      />
      {selectedReview && (
        <Stack spacing={2}>
          {reviewSaveError && (
            <Alert severity="error" data-testid="projects-panel-review-save-error">
              {reviewSaveError}
            </Alert>
          )}
          <InlineField label="Cycle" value={selectedReview.cycle_no} />
          <InlineField label="Planned date" value={formatDate(selectedReview.planned_date)} />
          <InlineField label="Due date" value={formatDate(selectedReview.due_date)} />
          <ReviewStatusInline
            value={selectedReview.status ?? null}
            onChange={handleReviewStatusChange}
            isSaving={updateReviewStatus.isPending}
            disabled={updateReviewStatus.isPending}
          />
          <InlineField label="Disciplines" value={selectedReview.disciplines} />
          <InlineField label="Deliverables" value={selectedReview.deliverables} />
          <InlineField label="Billed" value={selectedReview.is_billed ? 'Yes' : 'No'} />
        </Stack>
      )}
    </Stack>
  );
}

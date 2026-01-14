import { useMutation, useQueryClient } from '@tanstack/react-query';
import { serviceReviewsApi } from '@/api/services';
import type { ServiceReview } from '@/types/api';
import { toApiReviewStatus } from '@/utils/reviewStatus';

type UpdateReviewStatusArgs = {
  projectId: number;
  serviceId: number;
  reviewId: number;
  status: string | null;
};

type UpdateReviewStatusContext = {
  previousReviews?: ServiceReview[];
};

type UpdateReviewStatusResult = Awaited<ReturnType<typeof serviceReviewsApi.update>>;

const updateReviewList = (
  reviews: ServiceReview[] | undefined,
  reviewId: number,
  patch: Partial<ServiceReview>,
) => {
  if (!reviews) {
    return reviews;
  }
  return reviews.map((review) =>
    review.review_id === reviewId ? { ...review, ...patch } : review,
  );
};

export function useUpdateReviewStatus() {
  const queryClient = useQueryClient();

  return useMutation<UpdateReviewStatusResult, Error, UpdateReviewStatusArgs, UpdateReviewStatusContext>({
    mutationFn: ({ projectId, serviceId, reviewId, status }) =>
      serviceReviewsApi.update(projectId, serviceId, reviewId, { status: toApiReviewStatus(status) }),
    onMutate: async ({ projectId, serviceId, reviewId, status }) => {
      const nextStatus = toApiReviewStatus(status);
      const queryKey = ['serviceReviews', projectId, serviceId];

      await queryClient.cancelQueries({ queryKey });

      const previousReviews = queryClient.getQueryData<ServiceReview[]>(queryKey);

      queryClient.setQueryData<ServiceReview[]>(queryKey, (existing) =>
        updateReviewList(existing, reviewId, { status: nextStatus }),
      );

      return { previousReviews };
    },
    onError: (_err, vars, context) => {
      if (context?.previousReviews) {
        queryClient.setQueryData(['serviceReviews', vars.projectId, vars.serviceId], context.previousReviews);
      }
    },
    onSettled: (_data, _error, { projectId, serviceId }) => {
      queryClient.invalidateQueries({ queryKey: ['serviceReviews', projectId, serviceId] });
    },
  });
}

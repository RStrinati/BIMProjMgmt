import { useQuery, UseQueryOptions, QueryKey } from '@tanstack/react-query';

type UseEntityListOptions<T> = {
  queryKey: QueryKey;
  queryFn: () => Promise<T[]>;
  enabled?: boolean;
  options?: Omit<UseQueryOptions<T[]>, 'queryKey' | 'queryFn'>;
};

export function useEntityList<T>({ queryKey, queryFn, enabled = true, options }: UseEntityListOptions<T>) {
  return useQuery<T[]>({
    queryKey,
    queryFn,
    enabled,
    ...options,
  });
}

import { useQuery, UseQueryOptions, QueryKey } from '@tanstack/react-query';

type UseEntityDetailsOptions<T> = {
  queryKey: QueryKey;
  queryFn: () => Promise<T>;
  enabled?: boolean;
  options?: Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'>;
};

export function useEntityDetails<T>({ queryKey, queryFn, enabled = true, options }: UseEntityDetailsOptions<T>) {
  return useQuery<T>({
    queryKey,
    queryFn,
    enabled,
    ...options,
  });
}

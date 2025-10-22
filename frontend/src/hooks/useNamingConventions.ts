import { useQuery } from '@tanstack/react-query';
import { namingConventionsApi, type NamingConvention } from '../api/clients';

/**
 * Custom hook to fetch and cache naming conventions
 */
export const useNamingConventions = () => {
  return useQuery<NamingConvention[], Error>({
    queryKey: ['naming-conventions'],
    queryFn: namingConventionsApi.getAll,
    staleTime: 5 * 60 * 1000, // 5 minutes - naming conventions don't change often
  });
};

/**
 * Get formatted options for dropdowns
 */
export const useNamingConventionOptions = () => {
  const { data: conventions, ...rest } = useNamingConventions();
  
  const options = conventions?.map((conv) => ({
    value: conv.code,
    label: `${conv.name} (${conv.standard})`,
  })) || [];
  
  return {
    options,
    conventions,
    ...rest,
  };
};

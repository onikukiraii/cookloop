import { useQuery } from '@tanstack/react-query'
import { suggestApi } from '@/api/fetcher'

export const suggestKeys = {
  all: ['suggest'] as const,
  job: (jobId: number) => [...suggestKeys.all, 'job', jobId] as const,
  latest: [...['suggest'], 'latest'] as const,
}

export function useSuggestJob(jobId: number | null) {
  return useQuery({
    queryKey: suggestKeys.job(jobId ?? 0),
    queryFn: () => suggestApi.getJobStatus(jobId!),
    enabled: jobId != null,
    retry: 3,
    refetchInterval: (query) => {
      if (query.state.error) return false
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 2000
    },
  })
}

export function useLatestSuggestJob() {
  return useQuery({
    queryKey: suggestKeys.latest,
    queryFn: () => suggestApi.getLatestJob(),
    staleTime: 0,
  })
}

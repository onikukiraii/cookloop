import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { condimentsApi } from '@/api/fetcher'
import type { CondimentCreateParams, QuantityStatus } from '@/api/constants'

export const condimentKeys = {
  all: ['condiments'] as const,
  list: () => [...condimentKeys.all, 'list'] as const,
}

export function useCondiments() {
  return useQuery({
    queryKey: condimentKeys.list(),
    queryFn: () => condimentsApi.list(),
  })
}

export function useCreateCondiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: CondimentCreateParams) => condimentsApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: condimentKeys.all })
    },
  })
}

export function useUpdateCondiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, quantityStatus }: { id: number; quantityStatus: QuantityStatus }) =>
      condimentsApi.update(id, quantityStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: condimentKeys.all })
    },
  })
}

export function useDeleteCondiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => condimentsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: condimentKeys.all })
    },
  })
}

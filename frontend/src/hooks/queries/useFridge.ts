import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fridgeApi, ingredientsApi } from '@/api/fetcher'
import type { FridgeItemCreateParams, QuantityStatus } from '@/api/constants'
import { ingredientKeys } from './useIngredients'

export const fridgeKeys = {
  all: ['fridge'] as const,
  list: (q?: string) => [...fridgeKeys.all, 'list', q ?? ''] as const,
}

export function useFridgeItems(q?: string) {
  return useQuery({
    queryKey: fridgeKeys.list(q),
    queryFn: () => fridgeApi.list(q || undefined),
  })
}

export function useCreateFridgeItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: FridgeItemCreateParams) => fridgeApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fridgeKeys.all })
    },
  })
}

export function useUpdateFridgeItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, quantityStatus }: { id: number; quantityStatus: QuantityStatus }) =>
      fridgeApi.update(id, quantityStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fridgeKeys.all })
    },
  })
}

export function useDeleteFridgeItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => fridgeApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fridgeKeys.all })
    },
  })
}

export function useToggleStaple() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, isStaple }: { id: number; isStaple: boolean }) =>
      ingredientsApi.update(id, { is_staple: isStaple }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fridgeKeys.all })
      queryClient.invalidateQueries({ queryKey: ingredientKeys.all })
    },
  })
}

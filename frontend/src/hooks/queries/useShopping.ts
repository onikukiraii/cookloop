import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { shoppingApi } from '@/api/fetcher'
import type { ShoppingItemCreateParams } from '@/api/constants'

export const shoppingKeys = {
  all: ['shopping'] as const,
  list: () => [...shoppingKeys.all, 'list'] as const,
}

export function useShoppingItems() {
  return useQuery({
    queryKey: shoppingKeys.list(),
    queryFn: () => shoppingApi.list(),
  })
}

export function useCreateShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: ShoppingItemCreateParams) => shoppingApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shoppingKeys.all })
    },
  })
}

export function useCheckShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => shoppingApi.check(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shoppingKeys.all })
    },
  })
}

export function useDeleteShoppingItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => shoppingApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shoppingKeys.all })
    },
  })
}

export function useCreateShoppingItemByName() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: { name: string; source?: string }) => shoppingApi.createByName(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: shoppingKeys.all })
    },
  })
}

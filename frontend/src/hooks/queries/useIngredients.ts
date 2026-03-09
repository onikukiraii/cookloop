import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ingredientsApi } from '@/api/fetcher'
import type { IngredientMasterCreateParams } from '@/api/constants'

export const ingredientKeys = {
  all: ['ingredients'] as const,
  list: () => [...ingredientKeys.all, 'list'] as const,
}

export function useIngredients() {
  return useQuery({
    queryKey: ingredientKeys.list(),
    queryFn: () => ingredientsApi.list(),
  })
}

export function useCreateIngredient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (params: IngredientMasterCreateParams) => ingredientsApi.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ingredientKeys.all })
    },
  })
}

export function useUpdateIngredient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: number; body: { default_expiry_days?: number; is_staple?: boolean } }) =>
      ingredientsApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ingredientKeys.all })
    },
  })
}

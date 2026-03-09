import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { favoritesApi } from '@/api/fetcher'

export const favoriteKeys = {
  all: ['favorites'] as const,
  list: () => [...favoriteKeys.all, 'list'] as const,
}

export function useFavorites() {
  return useQuery({
    queryKey: favoriteKeys.list(),
    queryFn: () => favoritesApi.list(),
    select: (ids) => new Set(ids),
  })
}

export function useAddFavorite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (recipeId: number) => favoritesApi.add(recipeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all })
    },
  })
}

export function useRemoveFavorite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (recipeId: number) => favoritesApi.remove(recipeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: favoriteKeys.all })
    },
  })
}

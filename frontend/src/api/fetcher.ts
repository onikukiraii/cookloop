import createClient from 'openapi-fetch'
import type { paths } from './schema'
import type {
  IngredientMasterResponse,
  IngredientMasterCreateParams,
  FridgeItemResponse,
  FridgeItemCreateParams,
  FridgeItemUpdateParams,
  CondimentResponse,
  CondimentCreateParams,
  CondimentUpdateParams,
  ShoppingItemResponse,
  ShoppingItemCreateParams,
  QuantityStatus,
  SuggestParams,
  SuggestResponse,
  AddShoppingParams,
  AddShoppingResponse,
} from './constants'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const api = createClient<paths>({
  baseUrl: BASE_URL,
  fetch: async (input: Request) => {
    try {
      return await fetch(input)
    } catch {
      throw new Error('サーバーとの通信に失敗しました')
    }
  },
})

export function unwrap<T>(result: { data?: T; error?: unknown }): T {
  if (result.error !== undefined) {
    const err = result.error as Record<string, unknown>
    const message = typeof err.detail === 'string' ? err.detail : 'サーバーエラーが発生しました'
    throw new Error(message)
  }
  return result.data as T
}

export const ingredientsApi = {
  list: async () => {
    const res = await api.GET('/api/ingredients/')
    return unwrap<IngredientMasterResponse[]>(res)
  },
  create: async (body: IngredientMasterCreateParams) => {
    const res = await api.POST('/api/ingredients/', { body })
    return unwrap<IngredientMasterResponse>(res)
  },
  search: async (q: string): Promise<{ id: number; name: string; aliases?: string[]; yomi?: string }[]> => {
    const res = await fetch(`${BASE_URL}/api/ingredients/search?q=${encodeURIComponent(q)}`)
    if (!res.ok) throw new Error('検索に失敗しました')
    return res.json()
  },
  update: async (id: number, body: { default_expiry_days?: number; is_staple?: boolean }) => {
    const res = await fetch(`${BASE_URL}/api/ingredients/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'サーバーエラーが発生しました')
    }
    return res.json() as Promise<IngredientMasterResponse>
  },
}

export const fridgeApi = {
  list: async (q?: string) => {
    if (q) {
      const res = await fetch(`${BASE_URL}/api/fridge/?q=${encodeURIComponent(q)}`)
      if (!res.ok) throw new Error('検索に失敗しました')
      return res.json() as Promise<FridgeItemResponse[]>
    }
    const res = await api.GET('/api/fridge/')
    return unwrap<FridgeItemResponse[]>(res)
  },
  create: async (body: FridgeItemCreateParams) => {
    const res = await api.POST('/api/fridge/', { body })
    return unwrap<FridgeItemResponse>(res)
  },
  update: async (id: number, quantity_status: QuantityStatus) => {
    const res = await api.PATCH('/api/fridge/{item_id}', {
      params: { path: { item_id: id } },
      body: { quantity_status } as FridgeItemUpdateParams,
    })
    return unwrap<FridgeItemResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/api/fridge/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
}

export const condimentsApi = {
  list: async () => {
    const res = await api.GET('/api/condiments/')
    return unwrap<CondimentResponse[]>(res)
  },
  create: async (body: CondimentCreateParams) => {
    const res = await api.POST('/api/condiments/', { body })
    return unwrap<CondimentResponse>(res)
  },
  update: async (id: number, quantity_status: QuantityStatus) => {
    const res = await api.PATCH('/api/condiments/{item_id}', {
      params: { path: { item_id: id } },
      body: { quantity_status } as CondimentUpdateParams,
    })
    return unwrap<CondimentResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/api/condiments/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
}

export const shoppingApi = {
  list: async () => {
    const res = await api.GET('/api/shopping/')
    return unwrap<ShoppingItemResponse[]>(res)
  },
  create: async (body: ShoppingItemCreateParams) => {
    const res = await api.POST('/api/shopping/', { body })
    return unwrap<ShoppingItemResponse>(res)
  },
  check: async (id: number) => {
    const res = await api.PATCH('/api/shopping/{item_id}/check', {
      params: { path: { item_id: id } },
    })
    return unwrap<ShoppingItemResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/api/shopping/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
  createByName: async (body: { name: string; source?: string }): Promise<ShoppingItemResponse> => {
    const res = await fetch(`${BASE_URL}/api/shopping/by-name`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'サーバーエラーが発生しました')
    }
    return res.json() as Promise<ShoppingItemResponse>
  },
}

export const favoritesApi = {
  list: async (): Promise<number[]> => {
    const res = await fetch(`${BASE_URL}/api/favorites/`)
    if (!res.ok) throw new Error('お気に入りの取得に失敗しました')
    return res.json() as Promise<number[]>
  },
  add: async (recipeId: number): Promise<void> => {
    const res = await fetch(`${BASE_URL}/api/favorites/${recipeId}`, { method: 'POST' })
    if (!res.ok) throw new Error('お気に入りの追加に失敗しました')
  },
  remove: async (recipeId: number): Promise<void> => {
    const res = await fetch(`${BASE_URL}/api/favorites/${recipeId}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('お気に入りの解除に失敗しました')
  },
}

export const suggestApi = {
  suggest: async (body: SuggestParams): Promise<SuggestResponse> => {
    const res = await fetch(`${BASE_URL}/api/recipe/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'サーバーエラーが発生しました')
    }
    return res.json() as Promise<SuggestResponse>
  },
  addShopping: async (body: AddShoppingParams): Promise<AddShoppingResponse> => {
    const res = await fetch(`${BASE_URL}/api/recipe/suggest/add-shopping`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(typeof err.detail === 'string' ? err.detail : 'サーバーエラーが発生しました')
    }
    return res.json() as Promise<AddShoppingResponse>
  },
}

export { api }

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
    const res = await api.GET('/ingredients/')
    return unwrap<IngredientMasterResponse[]>(res)
  },
  create: async (body: IngredientMasterCreateParams) => {
    const res = await api.POST('/ingredients/', { body })
    return unwrap<IngredientMasterResponse>(res)
  },
  search: async (q: string): Promise<{ id: number; name: string; aliases?: string[]; yomi?: string }[]> => {
    const res = await fetch(`${BASE_URL}/ingredients/search?q=${encodeURIComponent(q)}`)
    if (!res.ok) throw new Error('検索に失敗しました')
    return res.json()
  },
  update: async (id: number, body: { default_expiry_days?: number; is_staple?: boolean }) => {
    const res = await fetch(`${BASE_URL}/ingredients/${id}`, {
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
      const res = await fetch(`${BASE_URL}/fridge/?q=${encodeURIComponent(q)}`)
      if (!res.ok) throw new Error('検索に失敗しました')
      return res.json() as Promise<FridgeItemResponse[]>
    }
    const res = await api.GET('/fridge/')
    return unwrap<FridgeItemResponse[]>(res)
  },
  create: async (body: FridgeItemCreateParams) => {
    const res = await api.POST('/fridge/', { body })
    return unwrap<FridgeItemResponse>(res)
  },
  update: async (id: number, quantity_status: QuantityStatus) => {
    const res = await api.PATCH('/fridge/{item_id}', {
      params: { path: { item_id: id } },
      body: { quantity_status } as FridgeItemUpdateParams,
    })
    return unwrap<FridgeItemResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/fridge/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
}

export const condimentsApi = {
  list: async () => {
    const res = await api.GET('/condiments/')
    return unwrap<CondimentResponse[]>(res)
  },
  create: async (body: CondimentCreateParams) => {
    const res = await api.POST('/condiments/', { body })
    return unwrap<CondimentResponse>(res)
  },
  update: async (id: number, quantity_status: QuantityStatus) => {
    const res = await api.PATCH('/condiments/{item_id}', {
      params: { path: { item_id: id } },
      body: { quantity_status } as CondimentUpdateParams,
    })
    return unwrap<CondimentResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/condiments/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
}

export const shoppingApi = {
  list: async () => {
    const res = await api.GET('/shopping/')
    return unwrap<ShoppingItemResponse[]>(res)
  },
  create: async (body: ShoppingItemCreateParams) => {
    const res = await api.POST('/shopping/', { body })
    return unwrap<ShoppingItemResponse>(res)
  },
  check: async (id: number) => {
    const res = await api.PATCH('/shopping/{item_id}/check', {
      params: { path: { item_id: id } },
    })
    return unwrap<ShoppingItemResponse>(res)
  },
  remove: async (id: number) => {
    await api.DELETE('/shopping/{item_id}', {
      params: { path: { item_id: id } },
    })
  },
}

export const suggestApi = {
  suggest: async (body: SuggestParams): Promise<SuggestResponse> => {
    const res = await fetch(`${BASE_URL}/recipe/suggest`, {
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
    const res = await fetch(`${BASE_URL}/recipe/suggest/add-shopping`, {
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

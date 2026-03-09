import type { components } from './schema'

export type IngredientMasterResponse = components['schemas']['IngredientMasterResponse']
export type IngredientMasterCreateParams = components['schemas']['IngredientMasterCreateParams']

export type FridgeItemResponse = components['schemas']['FridgeItemResponse']
export type FridgeItemCreateParams = components['schemas']['FridgeItemCreateParams']
export type FridgeItemUpdateParams = components['schemas']['FridgeItemUpdateParams']

export type CondimentResponse = components['schemas']['CondimentResponse']
export type CondimentCreateParams = components['schemas']['CondimentCreateParams']
export type CondimentUpdateParams = components['schemas']['CondimentUpdateParams']

export type ShoppingItemResponse = components['schemas']['ShoppingItemResponse']
export type ShoppingItemCreateParams = components['schemas']['ShoppingItemCreateParams']

export type QuantityStatus = components['schemas']['QuantityStatus']
export type ShoppingSource = components['schemas']['ShoppingSource']

export const QUANTITY_STATUS_LABEL: Record<QuantityStatus, string> = {
  full: 'たっぷり',
  half: '半分',
  little: '少し',
}

export const SHOPPING_SOURCE_LABEL: Record<ShoppingSource, string> = {
  manual: '手動追加',
  recipe: 'レシピから',
  staple_auto: '定番自動',
}

export type SuggestedStep = {
  step_order: number
  text: string
}

export type SuggestedMaterial = {
  name: string
  quantity: string | null
  group_name: string | null
}

export type SuggestedRecipe = {
  type: 'hotcook' | 'manual'
  name: string
  recipe_id: number | null
  menu_num: string | null
  image_url: string | null
  category: string
  used_ingredients: string[]
  missing_ingredients: string[]
  note: string
  steps: SuggestedStep[]
  materials: SuggestedMaterial[]
  manual_mode: string | null
  manual_stir: string | null
  manual_time_min: number | null
}

export type SuggestResponse = {
  suggestions: SuggestedRecipe[]
}

export type SuggestParams = {
  mode: 'omakase' | 'ingredient'
  ingredient_master_ids?: number[]
}

export type AddShoppingParams = {
  ingredient_names: string[]
}

export type AddShoppingResponse = {
  added_count: number
}

export type SuggestJobCreateResponse = {
  job_id: number
}

export type SuggestJobStatusResponse = {
  job_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  suggestions: SuggestedRecipe[] | null
  error: string | null
}

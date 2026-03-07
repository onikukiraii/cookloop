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

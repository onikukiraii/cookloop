import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSessionState } from '@/hooks/use-session-state'
import { ChefHat, ChevronDown, ChevronUp, CookingPot, Heart, RefreshCw, ShoppingCart, Sparkles, UtensilsCrossed } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { EmptyState } from '@/components/EmptyState'
import { ProgressBar } from '@/components/ProgressBar'
import { CookCompleteDialog } from '@/components/CookCompleteDialog'
import { favoritesApi, fridgeApi, suggestApi } from '@/api/fetcher'
import type { FridgeItemResponse, SuggestedRecipe } from '@/api/constants'

const CATEGORY_ORDER = ['主菜', '副菜', '汁物', '主食', 'デザート', 'その他'] as const

function groupByCategory(recipes: SuggestedRecipe[]): { category: string; recipes: SuggestedRecipe[] }[] {
  const groups = new Map<string, SuggestedRecipe[]>()
  for (const recipe of recipes) {
    const cat = recipe.category || 'その他'
    if (!groups.has(cat)) groups.set(cat, [])
    groups.get(cat)!.push(recipe)
  }
  return CATEGORY_ORDER
    .filter((cat) => groups.has(cat))
    .map((cat) => ({ category: cat, recipes: groups.get(cat)! }))
}

export function MenuSuggestPage() {
  const [fridgeItems, setFridgeItems] = useState<FridgeItemResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'omakase' | 'ingredient'>('omakase')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [suggestions, setSuggestions] = useSessionState<SuggestedRecipe[] | null>('menu-suggestions', null)
  const [suggesting, setSuggesting] = useState(false)
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [addingShoppingFor, setAddingShoppingFor] = useState<number | null>(null)
  const [favoriteIds, setFavoriteIds] = useState<Set<number>>(new Set())

  const toggleFavorite = async (recipeId: number) => {
    const isFav = favoriteIds.has(recipeId)
    setFavoriteIds((prev) => {
      const next = new Set(prev)
      if (isFav) next.delete(recipeId)
      else next.add(recipeId)
      return next
    })
    try {
      if (isFav) await favoritesApi.remove(recipeId)
      else await favoritesApi.add(recipeId)
    } catch {
      setFavoriteIds((prev) => {
        const next = new Set(prev)
        if (isFav) next.add(recipeId)
        else next.delete(recipeId)
        return next
      })
    }
  }

  const load = useCallback(async () => {
    try {
      const data = await fridgeApi.list()
      setFridgeItems(data)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    favoritesApi.list().then((ids) => setFavoriteIds(new Set(ids))).catch(() => {})
  }, [])

  const handleSuggest = async () => {
    setSuggesting(true)
    setSuggestions(null)
    setExpandedIndex(null)
    try {
      const res = await suggestApi.suggest({
        mode,
        ingredient_master_ids: mode === 'ingredient' ? selectedIds : [],
      })
      setSuggestions(res.suggestions)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '提案に失敗しました')
    } finally {
      setSuggesting(false)
    }
  }

  const handleAddShopping = async (index: number, names: string[]) => {
    setAddingShoppingFor(index)
    try {
      const res = await suggestApi.addShopping({ ingredient_names: names })
      if (res.added_count > 0) {
        toast.success(`${res.added_count}件を買い物リストに追加しました`)
      } else {
        toast.info('追加する食材はありませんでした（既に登録済み）')
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '追加に失敗しました')
    } finally {
      setAddingShoppingFor(null)
    }
  }

  const toggleIngredient = (id: number) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(v => v !== id) : [...prev, id]
    )
  }

  const canSuggest = mode === 'omakase' || selectedIds.length > 0

  const categorizedSuggestions = useMemo(
    () => suggestions ? groupByCategory(suggestions) : null,
    [suggestions],
  )

  // Build stable index map for RecipeCard keys
  const recipeIndexMap = useMemo(() => {
    if (!suggestions) return new Map<SuggestedRecipe, number>()
    const map = new Map<SuggestedRecipe, number>()
    suggestions.forEach((recipe, i) => map.set(recipe, i))
    return map
  }, [suggestions])

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">献立提案</h1>
        <p className="mt-1 text-sm text-muted-foreground">冷蔵庫の食材からAIが献立を提案します</p>
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground">読み込み中...</div>
      ) : fridgeItems.length === 0 ? (
        <EmptyState icon={<ChefHat className="h-10 w-10" />} message="冷蔵庫に食材を登録すると献立を提案できます" />
      ) : (
        <div className="space-y-6">
          <div className="rounded-lg border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-muted-foreground">冷蔵庫の食材（{fridgeItems.length}件）</h2>
            <div className="flex flex-wrap gap-2">
              {fridgeItems.map((item) => (
                <Badge key={item.id} variant="secondary">
                  {item.ingredient_name}
                </Badge>
              ))}
            </div>
          </div>

          <Tabs value={mode} onValueChange={(v) => { setMode(v as 'omakase' | 'ingredient'); setSuggestions(null) }}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="omakase">おまかせ</TabsTrigger>
              <TabsTrigger value="ingredient">食材指定</TabsTrigger>
            </TabsList>

            <TabsContent value="omakase" className="mt-4">
              <p className="mb-4 text-sm text-muted-foreground">
                冷蔵庫の全食材を考慮して、最適な献立を提案します。
              </p>
            </TabsContent>

            <TabsContent value="ingredient" className="mt-4">
              <p className="mb-3 text-sm text-muted-foreground">
                使いたい食材を選んでください。選んだ食材を優先的に使うレシピを提案します。
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                {fridgeItems.map((item) => (
                  <label
                    key={item.id}
                    className="flex cursor-pointer items-center gap-2 rounded-md border p-2 transition-colors hover:bg-accent has-[button[data-state=checked]]:border-primary has-[button[data-state=checked]]:bg-primary/5"
                  >
                    <Checkbox
                      checked={selectedIds.includes(item.ingredient_master_id)}
                      onCheckedChange={() => toggleIngredient(item.ingredient_master_id)}
                    />
                    <span className="text-sm">{item.ingredient_name}</span>
                  </label>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          <div className="flex flex-col items-center gap-2">
            <Button
              size="lg"
              disabled={suggesting || !canSuggest}
              onClick={handleSuggest}
              className="gap-2"
            >
              <Sparkles className="h-4 w-4" />
              献立を提案してもらう
            </Button>
            <ProgressBar visible={suggesting} />
          </div>

          {suggesting && (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="rounded-lg border p-4">
                  <Skeleton className="mb-3 h-6 w-48" />
                  <Skeleton className="mb-2 h-4 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ))}
            </div>
          )}

          {categorizedSuggestions && (
            <div className="space-y-6">
              <Tabs defaultValue={categorizedSuggestions[0]?.category}>
                <TabsList className="flex w-full">
                  {categorizedSuggestions.map((group) => (
                    <TabsTrigger key={group.category} value={group.category} className="flex-1">
                      {group.category}
                      <Badge variant="secondary" className="ml-1.5 px-1.5 py-0 text-[10px]">
                        {group.recipes.length}
                      </Badge>
                    </TabsTrigger>
                  ))}
                </TabsList>
                {categorizedSuggestions.map((group) => (
                  <TabsContent key={group.category} value={group.category} className="mt-4">
                    <div className="space-y-4">
                      {group.recipes.map((recipe) => {
                        const index = recipeIndexMap.get(recipe) ?? 0
                        return (
                          <RecipeCard
                            key={index}
                            recipe={recipe}
                            index={index}
                            expanded={expandedIndex === index}
                            onToggle={() => setExpandedIndex(expandedIndex === index ? null : index)}
                            onAddShopping={(names) => handleAddShopping(index, names)}
                            addingLoading={addingShoppingFor === index}
                            fridgeItems={fridgeItems}
                            onCookComplete={load}
                            isFavorite={recipe.recipe_id != null && favoriteIds.has(recipe.recipe_id)}
                            onToggleFavorite={recipe.recipe_id != null ? () => toggleFavorite(recipe.recipe_id!) : undefined}
                          />
                        )
                      })}
                    </div>
                  </TabsContent>
                ))}
              </Tabs>

              <div className="flex justify-center pt-2">
                <Button variant="outline" onClick={handleSuggest} disabled={suggesting} className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  別の候補を見る
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RecipeCard({
  recipe,
  index,
  expanded,
  onToggle,
  onAddShopping,
  addingLoading,
  fridgeItems,
  onCookComplete,
  isFavorite,
  onToggleFavorite,
}: {
  recipe: SuggestedRecipe
  index: number
  expanded: boolean
  onToggle: () => void
  onAddShopping: (names: string[]) => void
  addingLoading: boolean
  fridgeItems: FridgeItemResponse[]
  onCookComplete: () => void
  isFavorite: boolean
  onToggleFavorite?: () => void
}) {
  const [cookDialogOpen, setCookDialogOpen] = useState(false)
  const hasDetails = recipe.steps.length > 0 || recipe.materials.length > 0

  return (
    <div className="rounded-lg border bg-card shadow-sm">
      <div className="p-4">
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-muted-foreground/50">#{index + 1}</span>
            <h3 className="text-lg font-semibold">{recipe.name}</h3>
            {onToggleFavorite && (
              <button onClick={onToggleFavorite} className="shrink-0 p-0.5">
                <Heart
                  className={`h-5 w-5 transition-colors ${isFavorite ? 'fill-red-500 text-red-500' : 'text-muted-foreground hover:text-red-400'}`}
                />
              </button>
            )}
          </div>
          <Badge variant={recipe.type === 'hotcook' ? 'default' : 'secondary'}>
            {recipe.type === 'hotcook' ? (
              <><UtensilsCrossed className="mr-1 h-3 w-3" />ホットクック</>
            ) : (
              '手動調理'
            )}
          </Badge>
        </div>

        {recipe.type === 'hotcook' && recipe.menu_num && (
          <p className="mb-2 text-sm font-medium text-primary">メニュー番号: No.{recipe.menu_num}</p>
        )}

        {recipe.type === 'manual' && recipe.manual_mode && (
          <div className="mb-3 rounded-md bg-blue-50 p-3 dark:bg-blue-950/20">
            <span className="text-xs font-semibold text-blue-700 dark:text-blue-400">手動調理設定</span>
            <div className="mt-1.5 flex flex-wrap gap-2">
              <Badge variant="outline" className="border-blue-300 text-blue-700 dark:border-blue-600 dark:text-blue-400">
                {recipe.manual_mode}
              </Badge>
              {recipe.manual_stir && (
                <Badge variant="outline" className="border-blue-300 text-blue-700 dark:border-blue-600 dark:text-blue-400">
                  {recipe.manual_stir}
                </Badge>
              )}
              {recipe.manual_time_min != null && (
                <Badge variant="outline" className="border-blue-300 text-blue-700 dark:border-blue-600 dark:text-blue-400">
                  {recipe.manual_time_min}分
                </Badge>
              )}
            </div>
          </div>
        )}

        {recipe.image_url && (
          <img src={recipe.image_url} alt={recipe.name} className="mb-3 h-40 w-full rounded-md object-cover" />
        )}

        <div className="mb-2">
          <span className="text-xs font-medium text-muted-foreground">使用食材：</span>
          <div className="mt-1 flex flex-wrap gap-1">
            {recipe.used_ingredients.map((name) => (
              <Badge key={name} variant="outline" className="text-xs">
                {name}
              </Badge>
            ))}
          </div>
        </div>

        {recipe.note && (
          <p className="mb-2 text-sm text-muted-foreground">{recipe.note}</p>
        )}

        {recipe.missing_ingredients.length > 0 && (
          <div className="mb-2 rounded-md bg-amber-50 p-2 dark:bg-amber-950/20">
            <span className="text-xs font-medium text-amber-700 dark:text-amber-400">不足食材：</span>
            <div className="mt-1 flex flex-wrap items-center gap-1">
              {recipe.missing_ingredients.map((name) => (
                <Badge key={name} variant="outline" className="border-amber-300 text-xs text-amber-700 dark:border-amber-600 dark:text-amber-400">
                  {name}
                </Badge>
              ))}
              <Button
                variant="ghost"
                size="sm"
                className="ml-1 h-6 gap-1 text-xs"
                onClick={() => onAddShopping(recipe.missing_ingredients)}
                disabled={addingLoading}
              >
                <ShoppingCart className="h-3 w-3" />
                買い物リストに追加
              </Button>
            </div>
          </div>
        )}

          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={() => setCookDialogOpen(true)}
          >
            <CookingPot className="h-4 w-4" />
            作った！
          </Button>

          <CookCompleteDialog
            open={cookDialogOpen}
            onOpenChange={setCookDialogOpen}
            recipe={recipe}
            fridgeItems={fridgeItems}
            onComplete={onCookComplete}
          />
      </div>

      {hasDetails && (
        <>
          <button
            onClick={onToggle}
            className="flex w-full items-center justify-between border-t px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted/50"
          >
            {recipe.materials.length > 0 ? '材料・手順を見る' : '手順を見る'}
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {expanded && (
            <div className="border-t px-4 py-3 space-y-4">
              {recipe.materials.length > 0 && (
                <div>
                  <h4 className="mb-2 text-sm font-semibold">材料</h4>
                  <ul className="space-y-1">
                    {recipe.materials.map((mat, i) => (
                      <li key={i} className="flex items-baseline justify-between text-sm">
                        <span>
                          {mat.group_name && (
                            <Badge variant="outline" className="mr-1.5 text-[10px] px-1 py-0">{mat.group_name}</Badge>
                          )}
                          {mat.name}
                        </span>
                        {mat.quantity && (
                          <span className="ml-2 shrink-0 text-muted-foreground">{mat.quantity}</span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {recipe.steps.length > 0 && (
                <div>
                  {recipe.materials.length > 0 && <h4 className="mb-2 text-sm font-semibold">手順</h4>}
                  <ol className="space-y-2">
                    {recipe.steps.map((step) => (
                      <li key={step.step_order} className="flex gap-3 text-sm">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                          {step.step_order}
                        </span>
                        <span className="pt-0.5">{step.text}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

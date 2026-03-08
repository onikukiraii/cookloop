import { useCallback, useEffect, useState } from 'react'
import { Search, ExternalLink, ChefHat, ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { EmptyState } from '@/components/EmptyState'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

type RecipeListItem = {
  id: number
  code: string
  name: string
  menu_num: string | null
  image_url: string | null
  ingredient_names: string[]
}

type RecipeDetail = {
  id: number
  code: string
  name: string
  menu_num: string | null
  image_url: string | null
  source_url: string
  ingredients: { id: number; name: string }[]
  steps: { step_order: number; text: string }[]
}

async function searchRecipes(q: string): Promise<RecipeListItem[]> {
  const res = await fetch(`${BASE_URL}/recipes/?q=${encodeURIComponent(q)}`)
  if (!res.ok) throw new Error('検索に失敗しました')
  return res.json()
}

async function getRecipeDetail(id: number): Promise<RecipeDetail> {
  const res = await fetch(`${BASE_URL}/recipes/${id}`)
  if (!res.ok) throw new Error('レシピの取得に失敗しました')
  return res.json()
}

export function RecipePage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<RecipeListItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [detail, setDetail] = useState<RecipeDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([])
      setSearched(false)
      return
    }
    setLoading(true)
    setSearched(true)
    try {
      const data = await searchRecipes(q)
      setResults(data)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '検索に失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => handleSearch(query), 300)
    return () => clearTimeout(timer)
  }, [query, handleSearch])

  const openDetail = async (id: number) => {
    setDetailLoading(true)
    try {
      const data = await getRecipeDetail(id)
      setDetail(data)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '取得に失敗しました')
    } finally {
      setDetailLoading(false)
    }
  }

  if (detail) {
    return (
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <Button variant="ghost" size="sm" onClick={() => setDetail(null)} className="gap-1">
          <ArrowLeft className="h-4 w-4" />
          検索に戻る
        </Button>

        <div className="space-y-4">
          <div className="flex items-start gap-4">
            {detail.image_url && (
              <img
                src={detail.image_url}
                alt={detail.name}
                className="h-24 w-24 shrink-0 rounded-lg object-cover"
              />
            )}
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl font-bold tracking-tight">{detail.name}</h1>
              {detail.menu_num && (
                <p className="mt-1 text-sm text-muted-foreground">メニュー番号: {detail.menu_num}</p>
              )}
              <a
                href={detail.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-2 inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                <ExternalLink className="h-3.5 w-3.5" />
                元のレシピページ
              </a>
            </div>
          </div>

          <div className="rounded-lg border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-muted-foreground">材料</h2>
            <div className="flex flex-wrap gap-2">
              {detail.ingredients.map((ing) => (
                <Badge key={ing.id} variant="secondary">{ing.name}</Badge>
              ))}
              {detail.ingredients.length === 0 && (
                <p className="text-sm text-muted-foreground">材料情報がありません</p>
              )}
            </div>
          </div>

          <div className="rounded-lg border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-muted-foreground">調理手順</h2>
            {detail.steps.length > 0 ? (
              <ol className="space-y-3">
                {detail.steps.map((step) => (
                  <li key={step.step_order} className="flex gap-3">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                      {step.step_order}
                    </span>
                    <span className="text-sm leading-relaxed">{step.text}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-sm text-muted-foreground">手順情報がありません</p>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">レシピ検索</h1>
        <p className="mt-1 text-sm text-muted-foreground">料理名や食材名からホットクックレシピを検索</p>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="料理名・食材名で検索..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {loading || detailLoading ? (
        <div className="py-16 text-center text-muted-foreground">検索中...</div>
      ) : !searched ? (
        <EmptyState icon={<ChefHat className="h-10 w-10" />} message="キーワードを入力してレシピを検索" />
      ) : results.length === 0 ? (
        <EmptyState icon={<Search className="h-10 w-10" />} message="該当するレシピが見つかりませんでした" />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">{results.length}件のレシピ</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {results.map((recipe) => (
              <button
                key={recipe.id}
                onClick={() => openDetail(recipe.id)}
                className="flex items-start gap-3 rounded-lg border bg-card p-4 text-left shadow-sm transition-colors hover:bg-accent cursor-pointer"
              >
                {recipe.image_url && (
                  <img
                    src={recipe.image_url}
                    alt={recipe.name}
                    className="h-16 w-16 shrink-0 rounded-md object-cover"
                  />
                )}
                <div className="min-w-0 flex-1 space-y-2">
                  <p className="font-medium leading-tight">{recipe.name}</p>
                  {recipe.ingredient_names.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {recipe.ingredient_names.map((name) => (
                        <Badge key={name} variant="secondary" className="text-xs">
                          {name}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

import { useCallback, useEffect, useRef, useState } from 'react'
import { Plus, Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { ingredientsApi } from '@/api/fetcher'
import type { IngredientMasterResponse } from '@/api/constants'

interface IngredientSelectProps {
  ingredients: IngredientMasterResponse[]
  value: string
  onValueChange: (value: string) => void
  placeholder?: string
  onCreateNew?: (name: string) => void
}

export function IngredientSelect({ ingredients, value, onValueChange, placeholder = '食材を検索...', onCreateNew }: IngredientSelectProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<IngredientMasterResponse[]>([])
  const [open, setOpen] = useState(false)
  const [searching, setSearching] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null)

  const selectedName = ingredients.find((i) => String(i.id) === value)?.name ?? ''

  const searchIngredients = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults(ingredients)
      setSearching(false)
      return
    }
    setSearching(true)
    try {
      const hits = await ingredientsApi.search(q.trim())
      const hitIds = new Set(hits.map((h) => h.id))
      setResults(ingredients.filter((i) => hitIds.has(i.id)))
    } catch {
      setResults(ingredients.filter((i) => i.name.includes(q.trim())))
    } finally {
      setSearching(false)
    }
  }, [ingredients])

  useEffect(() => {
    if (!open) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => searchIngredients(query), 200)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [query, open, searchIngredients])

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (id: number, name: string) => {
    onValueChange(String(id))
    setQuery(name)
    setOpen(false)
  }

  const handleFocus = () => {
    setOpen(true)
    if (!query) setResults(ingredients)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value)
    onValueChange('')
    setOpen(true)
  }

  const handleCreateNew = () => {
    if (onCreateNew && query.trim()) {
      onCreateNew(query.trim())
      setQuery('')
      setOpen(false)
    }
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={value ? selectedName : query}
          onChange={handleInputChange}
          onFocus={handleFocus}
          placeholder={placeholder}
          className="pl-9"
        />
      </div>
      {open && (
        <div className="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover shadow-md">
          {searching ? (
            <div className="px-3 py-2 text-sm text-muted-foreground">検索中...</div>
          ) : results.length === 0 ? (
            <div className="space-y-1">
              <div className="px-3 py-2 text-sm text-muted-foreground">該当する食材がありません</div>
              {onCreateNew && query.trim() && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start gap-2 px-3"
                  onClick={handleCreateNew}
                >
                  <Plus className="h-4 w-4" />
                  「{query.trim()}」を新規登録して追加
                </Button>
              )}
            </div>
          ) : (
            results.map((item) => (
              <button
                key={item.id}
                type="button"
                className="flex w-full cursor-pointer items-center px-3 py-2 text-left text-sm hover:bg-accent"
                onClick={() => handleSelect(item.id, item.name)}
              >
                {item.name}
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}

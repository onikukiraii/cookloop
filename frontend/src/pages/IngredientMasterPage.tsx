import { useCallback, useEffect, useRef, useState } from 'react'
import { Plus, Leaf, Star, Search } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { EmptyState } from '@/components/EmptyState'
import type { IngredientMasterResponse } from '@/api/constants'
import { ingredientsApi } from '@/api/fetcher'
import { useIngredients, useCreateIngredient, useUpdateIngredient } from '@/hooks/queries/useIngredients'

export function IngredientMasterPage() {
  const { data: items = [], isLoading } = useIngredients()
  const createMutation = useCreateIngredient()
  const updateMutation = useUpdateIngredient()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [defaultExpiryDays, setDefaultExpiryDays] = useState('7')
  const [isStaple, setIsStaple] = useState(false)
  const [search, setSearch] = useState('')
  const [filteredIds, setFilteredIds] = useState<Set<number> | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(null)

  const doSearch = useCallback(async (q: string) => {
    if (!q.trim()) {
      setFilteredIds(null)
      return
    }
    try {
      const hits = await ingredientsApi.search(q.trim())
      setFilteredIds(new Set(hits.map((h) => h.id)))
    } catch {
      setFilteredIds(null)
    }
  }, [])

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => doSearch(search), 200)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
  }, [search, doSearch])

  const filtered = filteredIds === null
    ? items
    : items.filter((item: IngredientMasterResponse) => filteredIds.has(item.id))

  const handleToggleStaple = async (item: IngredientMasterResponse) => {
    try {
      await updateMutation.mutateAsync({ id: item.id, body: { is_staple: !item.is_staple } })
      toast.success(`「${item.name}」を${item.is_staple ? '定番から解除' : '定番に設定'}しました`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    }
  }

  const handleCreate = async () => {
    if (!name.trim()) return
    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        default_expiry_days: Number(defaultExpiryDays) || 7,
        is_staple: isStaple,
        category: 'ingredient',
      })
      toast.success(`「${name.trim()}」を登録しました`)
      setDialogOpen(false)
      setName('')
      setDefaultExpiryDays('7')
      setIsStaple(false)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '登録に失敗しました')
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">食材マスタ</h1>
          <p className="mt-1 text-sm text-muted-foreground">食材の基本情報を管理します</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-1 h-4 w-4" />
          追加
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="食材名で検索..."
          className="pl-9"
        />
      </div>

      {isLoading ? (
        <div className="py-16 text-center text-muted-foreground">読み込み中...</div>
      ) : filtered.length === 0 ? (
        <EmptyState icon={<Leaf className="h-10 w-10" />} message={search ? '該当する食材がありません' : '食材マスタが登録されていません'} />
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>食材名</TableHead>
                <TableHead className="w-32 text-center">賞味期限(日)</TableHead>
                <TableHead className="w-24 text-center">定番</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((item: IngredientMasterResponse) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.name}</TableCell>
                  <TableCell className="text-center">{item.default_expiry_days}</TableCell>
                  <TableCell className="text-center">
                    <button
                      onClick={() => handleToggleStaple(item)}
                      className="cursor-pointer rounded-md p-1 transition-colors hover:bg-muted"
                      title={item.is_staple ? '定番を解除' : '定番に設定'}
                    >
                      <Star
                        className={`h-5 w-5 ${item.is_staple ? 'fill-staple-flag text-staple-flag' : 'text-muted-foreground/40'}`}
                      />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>食材を追加</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">食材名</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="例: にんじん" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expiry">デフォルト賞味期限（日数）</Label>
              <Input
                id="expiry"
                type="number"
                min="1"
                value={defaultExpiryDays}
                onChange={(e) => setDefaultExpiryDays(e.target.value)}
              />
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="staple" checked={isStaple} onCheckedChange={(v) => setIsStaple(v === true)} />
              <Label htmlFor="staple">定番食材</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={createMutation.isPending}>
              キャンセル
            </Button>
            <Button onClick={handleCreate} disabled={!name.trim() || createMutation.isPending}>
              {createMutation.isPending ? '登録中...' : '登録'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

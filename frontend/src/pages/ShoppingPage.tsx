import { useCallback, useEffect, useState } from 'react'
import { Plus, ShoppingCart, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { EmptyState } from '@/components/EmptyState'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { IngredientSelect } from '@/components/IngredientSelect'
import { shoppingApi, ingredientsApi } from '@/api/fetcher'
import { SHOPPING_SOURCE_LABEL, type ShoppingItemResponse, type IngredientMasterResponse, type ShoppingSource } from '@/api/constants'

const sourceStyle: Record<string, string> = {
  manual: 'bg-shopping-manual/15 text-shopping-manual border-shopping-manual/30',
  recipe: 'bg-warm-400/15 text-warm-600 border-warm-400/30',
  staple_auto: 'bg-shopping-auto/15 text-shopping-auto border-shopping-auto/30',
}

export function ShoppingPage() {
  const [items, setItems] = useState<ShoppingItemResponse[]>([])
  const [ingredients, setIngredients] = useState<IngredientMasterResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [ingredientId, setIngredientId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ShoppingItemResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    try {
      const [shoppingData, ingredientData] = await Promise.all([
        shoppingApi.list(),
        ingredientsApi.list(),
      ])
      setItems(shoppingData)
      setIngredients(ingredientData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async () => {
    if (!ingredientId) return
    setSubmitting(true)
    try {
      await shoppingApi.create({
        ingredient_master_id: Number(ingredientId),
        source: 'manual' as ShoppingSource,
      })
      toast.success('買い物リストに追加しました')
      setDialogOpen(false)
      setIngredientId('')
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '追加に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  const handleCheck = async (item: ShoppingItemResponse) => {
    try {
      await shoppingApi.check(item.id)
      toast.success(`「${item.ingredient_name}」を購入済みにしました（冷蔵庫に登録されました）`)
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await shoppingApi.remove(deleteTarget.id)
      toast.success(`「${deleteTarget.ingredient_name}」を削除しました`)
      setDeleteTarget(null)
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '削除に失敗しました')
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">買い物リスト</h1>
          <p className="mt-1 text-sm text-muted-foreground">買い物リストを管理します</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-1 h-4 w-4" />
          追加
        </Button>
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground">読み込み中...</div>
      ) : items.length === 0 ? (
        <EmptyState icon={<ShoppingCart className="h-10 w-10" />} message="買い物リストは空です" />
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={false}
                  onCheckedChange={() => handleCheck(item)}
                />
                <span className="font-medium">{item.ingredient_name}</span>
                <Badge variant="outline" className={sourceStyle[item.source] ?? ''}>
                  {SHOPPING_SOURCE_LABEL[item.source as ShoppingSource] ?? item.source}
                </Badge>
              </div>
              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => setDeleteTarget(item)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>買い物リストに追加</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>食材</Label>
              <IngredientSelect ingredients={ingredients} value={ingredientId} onValueChange={setIngredientId} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>
              キャンセル
            </Button>
            <Button onClick={handleCreate} disabled={!ingredientId || submitting}>
              {submitting ? '追加中...' : '追加'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title="アイテムの削除"
        description={`「${deleteTarget?.ingredient_name}」を買い物リストから削除しますか？`}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  )
}

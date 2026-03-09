import { useState } from 'react'
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
import { SHOPPING_SOURCE_LABEL, type ShoppingItemResponse, type ShoppingSource } from '@/api/constants'
import { useShoppingItems, useCreateShoppingItem, useCheckShoppingItem, useDeleteShoppingItem, useCreateShoppingItemByName } from '@/hooks/queries/useShopping'
import { useIngredients } from '@/hooks/queries/useIngredients'

const sourceStyle: Record<string, string> = {
  manual: 'bg-shopping-manual/15 text-shopping-manual border-shopping-manual/30',
  recipe: 'bg-warm-400/15 text-warm-600 border-warm-400/30',
  staple_auto: 'bg-shopping-auto/15 text-shopping-auto border-shopping-auto/30',
}

export function ShoppingPage() {
  const { data: items = [], isLoading } = useShoppingItems()
  const { data: ingredients = [] } = useIngredients()
  const createMutation = useCreateShoppingItem()
  const createByNameMutation = useCreateShoppingItemByName()
  const checkMutation = useCheckShoppingItem()
  const deleteMutation = useDeleteShoppingItem()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [ingredientId, setIngredientId] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ShoppingItemResponse | null>(null)

  const handleCreate = async () => {
    if (!ingredientId) return
    try {
      await createMutation.mutateAsync({
        ingredient_master_id: Number(ingredientId),
        source: 'manual' as ShoppingSource,
      })
      toast.success('買い物リストに追加しました')
      setDialogOpen(false)
      setIngredientId('')
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '追加に失敗しました')
    }
  }

  const handleCheck = async (item: ShoppingItemResponse) => {
    try {
      await checkMutation.mutateAsync(item.id)
      toast.success(`「${item.ingredient_name}」を購入済みにしました（冷蔵庫に登録されました）`)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    }
  }

  const handleCreateByName = async (name: string) => {
    try {
      await createByNameMutation.mutateAsync({ name })
      toast.success(`「${name}」を新規登録して買い物リストに追加しました`)
      setDialogOpen(false)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '追加に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await deleteMutation.mutateAsync(deleteTarget.id)
      toast.success(`「${deleteTarget.ingredient_name}」を削除しました`)
      setDeleteTarget(null)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '削除に失敗しました')
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

      {isLoading ? (
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
        <DialogContent className="top-[10%] translate-y-0 max-h-[90dvh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>買い物リストに追加</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>食材</Label>
              <IngredientSelect ingredients={ingredients} value={ingredientId} onValueChange={setIngredientId} onCreateNew={handleCreateByName} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={createMutation.isPending}>
              キャンセル
            </Button>
            <Button onClick={handleCreate} disabled={!ingredientId || createMutation.isPending}>
              {createMutation.isPending ? '追加中...' : '追加'}
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
        loading={deleteMutation.isPending}
      />
    </div>
  )
}

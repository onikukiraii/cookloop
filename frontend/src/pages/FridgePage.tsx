import { useCallback, useEffect, useState } from 'react'
import { CircleCheck, Plus, Refrigerator, Search, Star } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { EmptyState } from '@/components/EmptyState'
import { QuantityBadge } from '@/components/QuantityBadge'
import { FreshnessBadge } from '@/components/FreshnessBadge'
import { getFreshness } from '@/lib/freshness'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { IngredientSelect } from '@/components/IngredientSelect'
import { fridgeApi, ingredientsApi } from '@/api/fetcher'
import { QUANTITY_STATUS_LABEL, type FridgeItemResponse, type IngredientMasterResponse, type QuantityStatus } from '@/api/constants'
import { cn } from '@/lib/utils'

const QUANTITY_CYCLE: QuantityStatus[] = ['full', 'half', 'little']

const freshnessBorder: Record<string, string> = {
  safe: 'border-l-freshness-safe',
  warning: 'border-l-freshness-warning',
  danger: 'border-l-freshness-danger',
  expired: 'border-l-freshness-expired',
}

export function FridgePage() {
  const [items, setItems] = useState<FridgeItemResponse[]>([])
  const [ingredients, setIngredients] = useState<IngredientMasterResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [ingredientId, setIngredientId] = useState('')
  const [expiryDate, setExpiryDate] = useState('')
  const [quantityStatus, setQuantityStatus] = useState<QuantityStatus>('full')
  const [submitting, setSubmitting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<FridgeItemResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async (q?: string) => {
    try {
      const [fridgeData, ingredientData] = await Promise.all([
        fridgeApi.list(q || undefined),
        ingredientsApi.list(),
      ])
      setItems(fridgeData)
      setIngredients(ingredientData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const delay = searchQuery ? 300 : 0
    const timer = setTimeout(() => {
      setLoading(true)
      load(searchQuery || undefined)
    }, delay)
    return () => clearTimeout(timer)
  }, [searchQuery, load])

  const handleCreate = async () => {
    if (!ingredientId) return
    setSubmitting(true)
    try {
      await fridgeApi.create({
        ingredient_master_id: Number(ingredientId),
        expiry_date: expiryDate || undefined,
        quantity_status: quantityStatus,
      })
      toast.success('食材を追加しました')
      setDialogOpen(false)
      resetForm()
      await load(searchQuery || undefined)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '追加に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  const handleQuantityToggle = async (item: FridgeItemResponse) => {
    const currentIndex = QUANTITY_CYCLE.indexOf(item.quantity_status as QuantityStatus)
    const nextStatus = QUANTITY_CYCLE[(currentIndex + 1) % QUANTITY_CYCLE.length]
    try {
      await fridgeApi.update(item.id, nextStatus)
      await load(searchQuery || undefined)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await fridgeApi.remove(deleteTarget.id)
      toast.success(`「${deleteTarget.ingredient_name}」を削除しました`)
      setDeleteTarget(null)
      await load(searchQuery || undefined)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '削除に失敗しました')
    } finally {
      setDeleting(false)
    }
  }

  const resetForm = () => {
    setIngredientId('')
    setExpiryDate('')
    setQuantityStatus('full')
  }

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr)
    return `${d.getMonth() + 1}/${d.getDate()}`
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">冷蔵庫</h1>
          <p className="mt-1 text-sm text-muted-foreground">冷蔵庫の中身を管理します</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-1 h-4 w-4" />
          追加
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="食材名で検索..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground">読み込み中...</div>
      ) : items.length === 0 ? (
        <EmptyState icon={<Refrigerator className="h-10 w-10" />} message="食材が登録されていません" />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {items.map((item) => {
            const freshness = getFreshness(item.expiry_date)
            return (
              <div
                key={item.id}
                className={cn(
                  'flex items-center justify-between rounded-lg border border-l-4 bg-card p-4 shadow-sm',
                  freshnessBorder[freshness],
                )}
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{item.ingredient_name}</span>
                    {item.is_staple && (
                      <span title="定番食材"><Star className="h-4 w-4 shrink-0 fill-staple-flag text-staple-flag" /></span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <FreshnessBadge expiryDate={item.expiry_date} />
                    <span className="text-xs text-muted-foreground">{formatDate(item.expiry_date)}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleQuantityToggle(item)}
                    className="cursor-pointer"
                    title={`残量を変更（現在: ${QUANTITY_STATUS_LABEL[item.quantity_status as QuantityStatus]}）`}
                  >
                    <QuantityBadge status={item.quantity_status as QuantityStatus} />
                  </button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-green-600" onClick={() => setDeleteTarget(item)} title="使い切り">
                    <CircleCheck className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>食材を追加</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>食材</Label>
              <IngredientSelect ingredients={ingredients} value={ingredientId} onValueChange={setIngredientId} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expiry">賞味期限（空欄でデフォルト値）</Label>
              <Input id="expiry" type="date" value={expiryDate} onChange={(e) => setExpiryDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label>残量</Label>
              <Select value={quantityStatus} onValueChange={(v) => setQuantityStatus(v as QuantityStatus)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUANTITY_CYCLE.map((s) => (
                    <SelectItem key={s} value={s}>{QUANTITY_STATUS_LABEL[s]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
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
        title="使い切り"
        description={`「${deleteTarget?.ingredient_name}」を使い切りにしますか？${deleteTarget?.is_staple ? '（定番食材のため買い物リストに自動追加されます）' : ''}`}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  )
}

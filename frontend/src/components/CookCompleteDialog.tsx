import { useEffect, useState } from 'react'
import { CircleCheck } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { QuantityBadge } from '@/components/QuantityBadge'
import { fridgeApi } from '@/api/fetcher'
import { QUANTITY_STATUS_LABEL, type FridgeItemResponse, type QuantityStatus, type SuggestedRecipe } from '@/api/constants'

const QUANTITY_CYCLE: QuantityStatus[] = ['full', 'half', 'little']

type ItemChange = {
  type: 'update'
  quantity_status: QuantityStatus
} | {
  type: 'remove'
}

interface CookCompleteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  recipe: SuggestedRecipe
  fridgeItems: FridgeItemResponse[]
  onComplete: () => void
}

export function CookCompleteDialog({ open, onOpenChange, recipe, fridgeItems, onComplete }: CookCompleteDialogProps) {
  const [changes, setChanges] = useState<Map<number, ItemChange>>(new Map())
  const [submitting, setSubmitting] = useState(false)

  const matchedItems = fridgeItems.filter(
    (item) => recipe.used_ingredients.includes(item.ingredient_name),
  )

  // ダイアログが開くたびにローカル状態をリセット
  useEffect(() => {
    if (open) setChanges(new Map())
  }, [open])

  const getDisplayStatus = (item: FridgeItemResponse): QuantityStatus | null => {
    const change = changes.get(item.id)
    if (!change) return item.quantity_status as QuantityStatus
    if (change.type === 'remove') return null
    return change.quantity_status
  }

  const handleQuantityToggle = (item: FridgeItemResponse) => {
    const currentStatus = getDisplayStatus(item)
    if (currentStatus === null) return
    const currentIndex = QUANTITY_CYCLE.indexOf(currentStatus)
    const nextStatus = QUANTITY_CYCLE[(currentIndex + 1) % QUANTITY_CYCLE.length]
    setChanges((prev) => {
      const next = new Map(prev)
      if (nextStatus === item.quantity_status) {
        next.delete(item.id)
      } else {
        next.set(item.id, { type: 'update', quantity_status: nextStatus })
      }
      return next
    })
  }

  const handleToggleRemove = (item: FridgeItemResponse) => {
    setChanges((prev) => {
      const next = new Map(prev)
      if (prev.get(item.id)?.type === 'remove') {
        next.delete(item.id)
      } else {
        next.set(item.id, { type: 'remove' })
      }
      return next
    })
  }

  const handleSubmit = async () => {
    if (changes.size === 0) {
      onOpenChange(false)
      return
    }
    setSubmitting(true)
    try {
      const promises: Promise<unknown>[] = []
      for (const [id, change] of changes) {
        if (change.type === 'update') {
          promises.push(fridgeApi.update(id, change.quantity_status))
        } else {
          promises.push(fridgeApi.remove(id))
        }
      }
      await Promise.all(promises)
      const removeCount = [...changes.values()].filter((c) => c.type === 'remove').length
      const updateCount = [...changes.values()].filter((c) => c.type === 'update').length
      const parts: string[] = []
      if (removeCount > 0) parts.push(`${removeCount}件を使い切り`)
      if (updateCount > 0) parts.push(`${updateCount}件の残量を更新`)
      toast.success(`${parts.join('、')}しました`)
      onComplete()
      onOpenChange(false)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  const hasChanges = changes.size > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>作った！食材を更新</DialogTitle>
          <DialogDescription>「{recipe.name}」の使用食材</DialogDescription>
        </DialogHeader>
        {matchedItems.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            冷蔵庫に該当する食材はありません
          </p>
        ) : (
          <div className="space-y-2">
            {matchedItems.map((item) => {
              const status = getDisplayStatus(item)
              const isRemoved = status === null
              return (
                <div
                  key={item.id}
                  className={`flex items-center justify-between rounded-lg border bg-card p-3 ${isRemoved ? 'opacity-40' : ''}`}
                >
                  <span className={`truncate font-medium ${isRemoved ? 'line-through' : ''}`}>
                    {item.ingredient_name}
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleQuantityToggle(item)}
                      className="cursor-pointer"
                      disabled={isRemoved}
                      title={isRemoved ? '使い切り予定' : `残量を変更（現在: ${QUANTITY_STATUS_LABEL[status]}）`}
                    >
                      <QuantityBadge status={isRemoved ? (item.quantity_status as QuantityStatus) : status} />
                    </button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className={`h-8 w-8 ${isRemoved ? 'text-green-600' : 'text-muted-foreground hover:text-green-600'}`}
                      onClick={() => handleToggleRemove(item)}
                      title={isRemoved ? '使い切りを取り消し' : '使い切り'}
                    >
                      <CircleCheck className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={submitting}>
            キャンセル
          </Button>
          <Button onClick={handleSubmit} disabled={submitting || !hasChanges}>
            {submitting ? '反映中...' : '反映する'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

import { useCallback, useEffect, useState } from 'react'
import { Plus, CookingPot, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { EmptyState } from '@/components/EmptyState'
import { QuantityBadge } from '@/components/QuantityBadge'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { condimentsApi } from '@/api/fetcher'
import { QUANTITY_STATUS_LABEL, type CondimentResponse, type QuantityStatus } from '@/api/constants'

const QUANTITY_CYCLE: QuantityStatus[] = ['full', 'half', 'little']

export function CondimentPage() {
  const [items, setItems] = useState<CondimentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [name, setName] = useState('')
  const [quantityStatus, setQuantityStatus] = useState<QuantityStatus>('full')
  const [isStaple, setIsStaple] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<CondimentResponse | null>(null)
  const [deleting, setDeleting] = useState(false)

  const load = useCallback(async () => {
    try {
      const data = await condimentsApi.list()
      setItems(data)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '読み込みに失敗しました')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleCreate = async () => {
    if (!name.trim()) return
    setSubmitting(true)
    try {
      await condimentsApi.create({
        name: name.trim(),
        quantity_status: quantityStatus,
        is_staple: isStaple,
      })
      toast.success(`「${name.trim()}」を登録しました`)
      setDialogOpen(false)
      setName('')
      setQuantityStatus('full')
      setIsStaple(true)
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '登録に失敗しました')
    } finally {
      setSubmitting(false)
    }
  }

  const handleQuantityToggle = async (item: CondimentResponse) => {
    const currentIndex = QUANTITY_CYCLE.indexOf(item.quantity_status as QuantityStatus)
    const nextStatus = QUANTITY_CYCLE[(currentIndex + 1) % QUANTITY_CYCLE.length]
    try {
      await condimentsApi.update(item.id, nextStatus)
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : '更新に失敗しました')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await condimentsApi.remove(deleteTarget.id)
      toast.success(`「${deleteTarget.name}」を削除しました`)
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
          <h1 className="text-2xl font-bold tracking-tight">調味料</h1>
          <p className="mt-1 text-sm text-muted-foreground">調味料の在庫を管理します</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-1 h-4 w-4" />
          追加
        </Button>
      </div>

      {loading ? (
        <div className="py-16 text-center text-muted-foreground">読み込み中...</div>
      ) : items.length === 0 ? (
        <EmptyState icon={<CookingPot className="h-10 w-10" />} message="調味料が登録されていません" />
      ) : (
        <div className="space-y-2">
          {items.map((item) => (
            <div key={item.id} className="flex items-center justify-between rounded-lg border bg-card p-4 shadow-sm">
              <div className="flex items-center gap-3">
                <span className="font-medium">{item.name}</span>
                {item.is_staple && (
                  <Badge className="bg-staple-flag/15 text-staple-flag border-staple-flag/30" variant="outline">
                    定番
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleQuantityToggle(item)}
                  className="cursor-pointer"
                  title={`残量を変更（現在: ${QUANTITY_STATUS_LABEL[item.quantity_status as QuantityStatus]}）`}
                >
                  <QuantityBadge status={item.quantity_status as QuantityStatus} />
                </button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive" onClick={() => setDeleteTarget(item)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>調味料を追加</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="condiment-name">名前</Label>
              <Input id="condiment-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="例: 醤油" />
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
            <div className="flex items-center space-x-2">
              <Checkbox id="condiment-staple" checked={isStaple} onCheckedChange={(v) => setIsStaple(v === true)} />
              <Label htmlFor="condiment-staple">定番調味料</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>
              キャンセル
            </Button>
            <Button onClick={handleCreate} disabled={!name.trim() || submitting}>
              {submitting ? '登録中...' : '登録'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}
        title="調味料の削除"
        description={`「${deleteTarget?.name}」を削除しますか？`}
        onConfirm={handleDelete}
        loading={deleting}
      />
    </div>
  )
}

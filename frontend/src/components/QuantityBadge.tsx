import { Badge } from '@/components/ui/badge'
import { QUANTITY_STATUS_LABEL, type QuantityStatus } from '@/api/constants'
import { cn } from '@/lib/utils'

const statusStyle: Record<QuantityStatus, string> = {
  full: 'bg-quantity-plenty/15 text-quantity-plenty border-quantity-plenty/30',
  half: 'bg-quantity-half/15 text-quantity-half border-quantity-half/30',
  little: 'bg-quantity-low/15 text-quantity-low border-quantity-low/30',
}

export function QuantityBadge({ status }: { status: QuantityStatus }) {
  return (
    <Badge variant="outline" className={cn('text-xs', statusStyle[status])}>
      {QUANTITY_STATUS_LABEL[status]}
    </Badge>
  )
}

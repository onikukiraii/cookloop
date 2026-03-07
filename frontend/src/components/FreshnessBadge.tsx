import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { getFreshness, type Freshness } from '@/lib/freshness'

const freshnessStyle: Record<Freshness, string> = {
  safe: 'bg-freshness-safe/15 text-freshness-safe border-freshness-safe/30',
  warning: 'bg-freshness-warning/15 text-freshness-warning border-freshness-warning/30',
  danger: 'bg-freshness-danger/15 text-freshness-danger border-freshness-danger/30',
  expired: 'bg-freshness-expired/15 text-freshness-expired border-freshness-expired/30',
}

const freshnessLabel: Record<Freshness, string> = {
  safe: '新鮮',
  warning: 'もうすぐ',
  danger: '期限間近',
  expired: '期限切れ',
}

export function FreshnessBadge({ expiryDate }: { expiryDate: string }) {
  const freshness = getFreshness(expiryDate)
  return (
    <Badge variant="outline" className={cn('text-xs', freshnessStyle[freshness])}>
      {freshnessLabel[freshness]}
    </Badge>
  )
}

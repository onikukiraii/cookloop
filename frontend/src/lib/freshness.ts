export type Freshness = 'safe' | 'warning' | 'danger' | 'expired'

export function getFreshness(expiryDate: string): Freshness {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const expiry = new Date(expiryDate)
  expiry.setHours(0, 0, 0, 0)
  const diffDays = Math.ceil((expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return 'expired'
  if (diffDays <= 1) return 'danger'
  if (diffDays <= 3) return 'warning'
  return 'safe'
}

import type { ReactNode } from 'react'

export function EmptyState({ icon, message }: { icon?: ReactNode; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border bg-muted/30 py-16 text-muted-foreground">
      {icon && <div className="mb-3 text-4xl">{icon}</div>}
      <p className="text-lg font-medium">{message}</p>
    </div>
  )
}

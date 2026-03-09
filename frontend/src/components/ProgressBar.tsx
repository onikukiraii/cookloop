import { useProgressMessage } from '@/hooks/use-progress-message'

export function ProgressBar({ visible }: { visible: boolean }) {
  const message = useProgressMessage(visible)

  if (!visible) return null

  return (
    <div className="flex flex-col items-center gap-3 py-4">
      <div className="h-1.5 w-full max-w-xs overflow-hidden rounded-full bg-primary/20">
        <div className="h-full w-1/3 animate-[progress_1.5s_ease-in-out_infinite] rounded-full bg-primary" />
      </div>
      <p className="text-sm font-medium text-muted-foreground animate-in fade-in duration-300">
        {message}
      </p>
    </div>
  )
}

import { useCallback, useEffect, useRef, useSyncExternalStore } from 'react'

const PROGRESS_MESSAGES = [
  '冷蔵庫の食材を確認しています...',
  '食材の残量と期限をチェック中...',
  'ホットクックのレシピを検索中...',
  '食材の組み合わせを分析中...',
  'AIが献立を組み立てています...',
  '栄養バランスを調整中...',
  '最適な献立を選んでいます...',
]

// 最後まで到達した後にループ表示するメッセージ
const WAITING_MESSAGES = [
  'あと少しで完成します...',
  '最終チェックをしています...',
]

const MESSAGE_INTERVAL_MS = 3000

function useProgressMessage(active: boolean) {
  const indexRef = useRef(0)
  const listenersRef = useRef(new Set<() => void>())

  useEffect(() => {
    if (!active) {
      indexRef.current = 0
      for (const l of listenersRef.current) l()
      return
    }
    indexRef.current = 0
    const id = window.setInterval(() => {
      indexRef.current += 1
      for (const l of listenersRef.current) l()
    }, MESSAGE_INTERVAL_MS)
    return () => window.clearInterval(id)
  }, [active])

  const subscribe = useCallback((cb: () => void) => {
    listenersRef.current.add(cb)
    return () => { listenersRef.current.delete(cb) }
  }, [])

  const getSnapshot = useCallback(() => indexRef.current, [])

  const rawIndex = useSyncExternalStore(subscribe, getSnapshot)

  if (rawIndex < PROGRESS_MESSAGES.length) {
    return PROGRESS_MESSAGES[rawIndex]
  }
  const waitingIndex = (rawIndex - PROGRESS_MESSAGES.length) % WAITING_MESSAGES.length
  return WAITING_MESSAGES[waitingIndex]
}

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

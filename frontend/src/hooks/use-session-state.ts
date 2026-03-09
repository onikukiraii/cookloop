import { useCallback, useSyncExternalStore } from 'react'

// 同じキーを使う全コンポーネントに変更を通知するためのリスナー管理
const listeners = new Map<string, Set<() => void>>()

function subscribe(key: string, listener: () => void) {
  if (!listeners.has(key)) listeners.set(key, new Set())
  listeners.get(key)!.add(listener)
  return () => { listeners.get(key)?.delete(listener) }
}

function emitChange(key: string) {
  listeners.get(key)?.forEach((l) => l())
}

// getSnapshot の参照安定性を保つためのキャッシュ
const cache = new Map<string, { raw: string | null; parsed: unknown }>()

function getSnapshot<T>(key: string, initialValue: T): T {
  const raw = sessionStorage.getItem(key)
  const cached = cache.get(key)
  if (cached && cached.raw === raw) return cached.parsed as T

  let parsed: T
  if (raw === null) {
    parsed = initialValue
  } else {
    try {
      parsed = JSON.parse(raw) as T
    } catch {
      parsed = initialValue
    }
  }
  cache.set(key, { raw, parsed })
  return parsed
}

export function useSessionState<T>(key: string, initialValue: T) {
  const value = useSyncExternalStore(
    (listener) => subscribe(key, listener),
    () => getSnapshot(key, initialValue),
  )

  const set = useCallback((newValue: T | ((prev: T) => T)) => {
    const prev = getSnapshot(key, initialValue)
    const resolved = newValue instanceof Function ? newValue(prev) : newValue
    if (resolved === null || resolved === undefined) {
      sessionStorage.removeItem(key)
    } else {
      sessionStorage.setItem(key, JSON.stringify(resolved))
    }
    // キャッシュを即座に更新して参照安定性を保つ
    const newRaw = sessionStorage.getItem(key)
    cache.set(key, { raw: newRaw, parsed: resolved })
    emitChange(key)
  }, [key, initialValue])

  return [value, set] as const
}

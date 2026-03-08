import { useState, useCallback } from 'react'

export function useSessionState<T>(key: string, initialValue: T) {
  const [value, setValue] = useState<T>(() => {
    const stored = sessionStorage.getItem(key)
    if (stored === null) return initialValue
    try {
      return JSON.parse(stored) as T
    } catch {
      return initialValue
    }
  })

  const set = useCallback((newValue: T | ((prev: T) => T)) => {
    setValue((prev) => {
      const resolved = newValue instanceof Function ? newValue(prev) : newValue
      if (resolved === null || resolved === undefined) {
        sessionStorage.removeItem(key)
      } else {
        sessionStorage.setItem(key, JSON.stringify(resolved))
      }
      return resolved
    })
  }, [key])

  return [value, set] as const
}

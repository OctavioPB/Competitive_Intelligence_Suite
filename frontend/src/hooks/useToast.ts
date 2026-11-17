import { useCallback, useEffect, useRef, useState } from 'react'

export type ToastType = 'success' | 'error' | 'warning'
export interface ToastState {
  msg: string
  type: ToastType
}

/** Transient status message that clears itself (and its timer on unmount). */
export function useToast(durationMs = 5000) {
  const [toast, setToast] = useState<ToastState | null>(null)
  const timer = useRef<number>()

  const showToast = useCallback(
    (msg: string, type: ToastType) => {
      window.clearTimeout(timer.current)
      setToast({ msg, type })
      timer.current = window.setTimeout(() => setToast(null), durationMs)
    },
    [durationMs],
  )

  useEffect(() => () => window.clearTimeout(timer.current), [])

  return { toast, showToast }
}

/** Human-readable message from a rejected api call. */
export function errorMessage(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback
}

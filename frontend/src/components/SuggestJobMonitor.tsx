import { useCallback, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { ChefHat, Loader2 } from 'lucide-react'
import { useSessionState } from '@/hooks/use-session-state'
import { useSuggestJob } from '@/hooks/queries/useSuggest'
import { useProgressMessage } from '@/hooks/use-progress-message'
import type { SuggestedRecipe } from '@/api/constants'

export function SuggestJobMonitor() {
  const [jobId, setJobId] = useSessionState<number | null>('suggest-job-id', null)
  const [, setSuggestions] = useSessionState<SuggestedRecipe[] | null>('menu-suggestions', null)
  const { data: jobStatus, error: jobError } = useSuggestJob(jobId)
  const location = useLocation()
  const navigate = useNavigate()

  const isOnSuggestPage = location.pathname === '/menu-suggest'
  const isRunning = jobId != null && !jobError && (jobStatus?.status === 'pending' || jobStatus?.status === 'running' || !jobStatus)
  const message = useProgressMessage(isRunning)

  const sendNotification = useCallback((title: string, body: string) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/pwa-192x192.png' })
    }
  }, [])

  useEffect(() => {
    if (jobError) {
      toast.error('提案状況の取得に失敗しました。再度お試しください。')
      setJobId(null)
      return
    }
    if (!jobStatus) return
    if (jobStatus.status === 'completed' && jobStatus.suggestions) {
      setSuggestions(jobStatus.suggestions)
      setJobId(null)
      sendNotification('献立提案が完了しました', `${jobStatus.suggestions.length}品の献立が提案されました`)
      if (!isOnSuggestPage) {
        toast('献立提案が完了しました', {
          description: `${jobStatus.suggestions.length}品の献立が提案されました`,
          action: {
            label: '見る',
            onClick: () => navigate('/menu-suggest'),
          },
          icon: <ChefHat className="h-4 w-4" />,
          duration: 8000,
        })
      }
    } else if (jobStatus.status === 'failed') {
      toast.error(jobStatus.error ?? '提案処理中にエラーが発生しました')
      setJobId(null)
      sendNotification('献立提案に失敗しました', jobStatus.error ?? 'エラーが発生しました')
    }
  }, [jobStatus, jobError, setSuggestions, setJobId, sendNotification, isOnSuggestPage, navigate])

  // 献立ページでは ProgressBar が表示されるのでフロートは出さない
  if (!isRunning || isOnSuggestPage) return null

  return (
    <button
      onClick={() => navigate('/menu-suggest')}
      className="fixed bottom-20 right-4 z-50 flex items-center gap-2.5 rounded-full border bg-background/95 px-4 py-2.5 shadow-lg backdrop-blur-sm transition-transform hover:scale-105 active:scale-95 md:bottom-6"
    >
      <Loader2 className="h-4 w-4 animate-spin text-primary" />
      <span className="max-w-[180px] truncate text-xs font-medium text-muted-foreground">
        {message}
      </span>
    </button>
  )
}

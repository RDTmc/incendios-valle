import { useState, useEffect } from 'react'
import { AlertTriangle, X, Flame, Info } from 'lucide-react'

interface Alert {
  id: number
  alert_type: string
  message: string
  report_id: string
  latitud: number
  longitud: number
  source: string
  read: boolean
  created_at: string
}

const alertColors: Record<string, string> = {
  CRITICO: 'bg-red-600 border-red-800',
  ALTA: 'bg-orange-500 border-orange-700',
  MEDIA: 'bg-yellow-500 border-yellow-700',
  INFO: 'bg-blue-500 border-blue-700',
}

const alertIcons: Record<string, React.ReactNode> = {
  CRITICO: <AlertTriangle className="w-5 h-5 text-white" />,
  ALTA: <Flame className="w-5 h-5 text-white" />,
  MEDIA: <AlertTriangle className="w-5 h-5 text-yellow-100" />,
  INFO: <Info className="w-5 h-5 text-white" />,
}

const POLL_INTERVAL = 30000

export default function AlertBanner() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [dismissed, setDismissed] = useState<Set<number>>(new Set())

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const data = await fetch(`${import.meta.env.VITE_API_URL || 'https://api.keogh.lat/api'}/alerts?read=0&limit=5`)
        if (data.ok) {
          const json = await data.json()
          setAlerts(json)
        }
      } catch {
        // silent fail
      }
    }
    fetchAlerts()
    const interval = setInterval(fetchAlerts, POLL_INTERVAL)
    return () => clearInterval(interval)
  }, [])

  const dismiss = (id: number) => {
    setDismissed(prev => new Set(prev).add(id))
    fetch(`${import.meta.env.VITE_API_URL || 'https://api.keogh.lat/api'}/alerts/${id}/read`, { method: 'PUT' })
      .catch(() => {})
  }

  const visibleAlerts = alerts.filter(a => !dismissed.has(a.id))

  if (visibleAlerts.length === 0) return null

  return (
    <div className="fixed bottom-20 left-4 right-4 z-50 flex flex-col gap-2 max-w-md mx-auto">
      {visibleAlerts.map(alert => (
        <div
          key={alert.id}
          className={`flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg text-white ${alertColors[alert.alert_type] || alertColors.INFO} animate-slide-in`}
          role="alert"
        >
          <span className="flex-shrink-0 mt-0.5">{alertIcons[alert.alert_type] || alertIcons.INFO}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{alert.alert_type}</p>
            <p className="text-xs opacity-90">{alert.message}</p>
          </div>
          <button onClick={() => dismiss(alert.id)} className="text-white/70 hover:text-white flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  )
}

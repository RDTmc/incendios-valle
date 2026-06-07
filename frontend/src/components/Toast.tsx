import { useToast } from '../util/toast'

const typeStyles: Record<string, string> = {
  success: 'bg-green-600 text-white',
  error: 'bg-red-600 text-white',
  warning: 'bg-yellow-500 text-black',
  info: 'bg-blue-600 text-white',
}

const typeIcons: Record<string, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
}

export default function ToastContainer() {
  const { toasts, removeToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map(toast => (
        <div
          key={toast.id}
          className={`flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg transition-all duration-300 animate-slide-in ${typeStyles[toast.type]}`}
          role="alert"
        >
          <span className="text-lg font-bold flex-shrink-0">{typeIcons[toast.type]}</span>
          <p className="text-sm flex-1">{toast.message}</p>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-white/80 hover:text-white flex-shrink-0 ml-2"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  )
}

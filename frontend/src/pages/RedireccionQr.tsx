import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const URL_BASE = 'https://incendios-valle.pages.dev'
const INTENT_ANDROID =
  'intent://incendios-valle.pages.dev/' +
  '?utm_source=afiche_municipal&utm_medium=qr' +
  '#Intent;scheme=https;package=com.android.chrome;end'

function esAndroid(): boolean {
  return /android/i.test(navigator.userAgent)
}

export default function RedireccionQr() {
  const navigate = useNavigate()
  const [estado, setEstado] = useState('redirigiendo')

  useEffect(() => {
    if (esAndroid()) {
      setEstado('android')
      // Fuerza salida del visor interno abriendo Chrome nativo
      window.location.href = INTENT_ANDROID
      // Fallback: si intent:// no funciona, redirige HTTP tras 2s
      const fallback = setTimeout(() => {
        window.location.href = `${URL_BASE}/login`
      }, 2000)
      return () => clearTimeout(fallback)
    }

    // iOS u otros → redirección limpia al login
    setEstado('redirigiendo')
    navigate('/login', { replace: true })
  }, [navigate])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="text-center max-w-sm">
        <div className="w-16 h-16 bg-fire-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <span className="text-white text-3xl">🔥</span>
        </div>
        {estado === 'android' ? (
          <>
            <p className="text-gray-700 font-medium">
              Abriendo Chrome...
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Si no se abre automáticamente,{' '}
              <a
                href="/login"
                className="text-fire-500 underline"
                onClick={(e) => { e.preventDefault(); navigate('/login', { replace: true }) }}
              >
                presiona aquí
              </a>
            </p>
          </>
        ) : (
          <>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-fire-500 mx-auto mb-3" />
            <p className="text-gray-600 text-sm">Redirigiendo...</p>
          </>
        )}
      </div>
    </div>
  )
}

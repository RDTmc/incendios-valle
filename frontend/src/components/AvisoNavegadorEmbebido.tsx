import { useState, useEffect } from 'react'
import { detectarNavegadorEmbebido, esNavegadorInstalable } from '../util/navegador'

export default function AvisoNavegadorEmbebido() {
  const [visible, setVisible] = useState(false)
  const [aplicacion, setAplicacion] = useState<string | null>(null)

  useEffect(() => {
    const embebido = detectarNavegadorEmbebido()
    const instalada = esNavegadorInstalable()
    if (embebido && !instalada) {
      setAplicacion(embebido)
      setVisible(true)
    }
  }, [])

  if (!visible) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-50 border-b-2 border-yellow-400 shadow-lg p-3 pt-6">
      <div className="max-w-lg mx-auto flex items-start gap-2">
        <span className="text-xl shrink-0">🧭</span>
        <p className="text-sm text-yellow-900 leading-snug">
          Detectamos que estás usando <strong>{aplicacion}</strong>. 
          Para guardar esta aplicación en tu teléfono, presiona el menú de opciones 
          de tu escáner y selecciona <strong>‘Abrir en el navegador del sistema’</strong> (Chrome/Safari).
        </p>
        <button
          onClick={() => setVisible(false)}
          className="shrink-0 text-yellow-700 hover:text-yellow-900 font-bold text-lg leading-none"
          aria-label="Cerrar"
        >
          ×
        </button>
      </div>
    </div>
  )
}

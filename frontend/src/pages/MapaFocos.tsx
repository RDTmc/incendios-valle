import { useState, useEffect } from 'react'
import { API } from '../api'

interface FocoActivo {
  id: string
  lat: number
  lng: number
  estado: string
  tipo: string
  created_at: string
}

const estadoColor = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return 'bg-red-100 text-red-700'
    case 'CONTROLADO': return 'bg-orange-100 text-orange-700'
    case 'EXTINGUIDO': return 'bg-green-100 text-green-700'
    default:           return 'bg-gray-100 text-gray-700'
  }
}

const estadoDot = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return 'bg-red-500'
    case 'CONTROLADO': return 'bg-orange-500'
    case 'EXTINGUIDO': return 'bg-green-500'
    default:           return 'bg-gray-400'
  }
}

export default function MapaFocos() {
  const [focos, setFocos] = useState<FocoActivo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const abort = new AbortController()
    const mounted = true
    setLoading(true)
    setError(null)
    API.getFocosActivos()
      .then((data) => {
        if (mounted) setFocos(data)
      })
      .catch((err) => {
        if (mounted && err.name !== 'AbortError') setError(err.message || 'Error al cargar focos activos')
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => abort.abort()
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-fire-500 text-white p-4">
        <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
        <p className="text-sm opacity-90">{loading ? 'Cargando...' : `${focos.length} focos en tiempo real`}</p>
      </div>

      <div className="h-[calc(100vh-140px)] bg-gray-200 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-fire-500 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">Cargando focos activos...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50">
            <div className="text-center max-w-xs">
              <span className="text-4xl">⚠️</span>
              <p className="text-red-600 mt-2 text-sm font-medium">Error</p>
              <p className="text-gray-600 text-xs mt-1">{error}</p>
              <button
                onClick={() => {
                  setLoading(true)
                  setError(null)
                  API.getFocosActivos()
                    .then(setFocos)
                    .catch((err) => setError(err.message))
                    .finally(() => setLoading(false))
                }}
                className="mt-3 px-4 py-1.5 bg-fire-500 text-white text-sm rounded hover:bg-fire-600"
              >
                Reintentar
              </button>
            </div>
          </div>
        )}

        {!loading && !error && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <span className="text-6xl">🗺️</span>
              <p className="text-gray-600 mt-4">Mapa de Google (integración pendiente)</p>
              <p className="text-xs text-gray-500">{focos.length} focos cargados desde DynamoDB</p>
            </div>
          </div>
        )}

        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3">
          <h3 className="text-sm font-semibold mb-2">Leyenda:</h3>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-xs">Activo</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-orange-500 rounded-full" />
              <span className="text-xs">Controlado</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-xs">Extinguido</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-4 border-t">
        <h3 className="font-semibold mb-3">Focos Recientes:</h3>
        {focos.length === 0 && !loading ? (
          <p className="text-sm text-gray-500 text-center py-4">No hay focos registrados</p>
        ) : (
          <div className="space-y-2">
            {focos.map((foco) => (
              <div key={foco.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div>
                  <p className="font-medium text-sm">
                    <span className={`inline-block w-2.5 h-2.5 rounded-full ${estadoDot(foco.estado)} mr-2`} />
                    {foco.tipo}
                  </p>
                  <p className="text-xs text-gray-500">
                    {foco.lat.toFixed(4)}, {foco.lng.toFixed(4)}
                  </p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${estadoColor(foco.estado)}`}>
                  {foco.estado}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
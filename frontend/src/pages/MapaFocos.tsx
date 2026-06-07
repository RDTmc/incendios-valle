import { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import type { MapRef } from 'react-map-gl/mapbox'
import { useLocation } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { API } from '../api'
import type { MapStrategy, FocoData } from '../util/map'
import { MapboxStrategy } from '../util/map'

const VALLE_DEL_SOL: [number, number] = [-33.4489, -70.6693]
const RADIO_MAX_KM = 50
const HORAS_VENTANA = 24

function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

const estadoDot = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return '#dc2626'
    case 'PENDIENTE':  return '#d97706'
    case 'CONTROLADO': return '#f97316'
    case 'EXTINGUIDO': return '#16a34a'
    default:           return '#9ca3af'
  }
}

const estadoColor = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return 'bg-red-100 text-red-700'
    case 'PENDIENTE':  return 'bg-amber-100 text-amber-700'
    case 'CONTROLADO': return 'bg-orange-100 text-orange-700'
    case 'EXTINGUIDO': return 'bg-green-100 text-green-700'
    default:           return 'bg-gray-100 text-gray-700'
  }
}

const tipoLabel = (tipo: string) =>
  tipo.toLowerCase() === 'forestal' ? 'Forestal' : 'Urbano'

const strategies: MapStrategy[] = [new MapboxStrategy()]

export default function MapaFocos() {
  const [strategyIdx, setStrategyIdx] = useState(0)
  const strategy = strategies[strategyIdx]
  const mapRef = useRef<any>(null)

  const location = useLocation()
  const state = location.state as { centerTo?: [number, number]; highlightId?: string } | null
  const centerTo = state?.centerTo ?? null
  const highlightId = state?.highlightId ?? null

  const [focos, setFocos] = useState<FocoData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFoco, setSelectedFoco] = useState<FocoData | null>(null)
  const [misIds] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem('mis_reportes_ids')
      return stored ? JSON.parse(stored) : []
    } catch { return [] }
  })
  const misReportesCount = misIds.length
  const misIdSet = useMemo(() => new Set(misIds), [misIds])

  useEffect(() => {
    const ab = new AbortController()
    setLoading(true)
    setError(null)
    API.getFocosActivos()
      .then((data: FocoData[]) => {
        if (!ab.signal.aborted) setFocos(data)
      })
      .catch((err: Error) => {
        if (!ab.signal.aborted) setError(err.message || 'Error al cargar focos activos')
      })
      .finally(() => {
        if (!ab.signal.aborted) setLoading(false)
      })
    return () => ab.abort()
  }, [])

  const handleRetry = useCallback(() => {
    setLoading(true)
    setError(null)
    API.getFocosActivos()
      .then((data: FocoData[]) => setFocos(data))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const flyToFoco = useCallback((foco: FocoData) => {
    if (mapRef.current && typeof mapRef.current.flyTo === 'function') {
      mapRef.current.flyTo({ center: [foco.lng, foco.lat], zoom: 14, duration: 1000 })
    }
  }, [])

  const handleMapReady = useCallback((ref: any) => {
    mapRef.current = ref
  }, [])

  const focosFiltrados = useMemo(() => {
    const corte = Date.now() - HORAS_VENTANA * 60 * 60 * 1000
    const VALID_ESTADOS = new Set(['ACTIVO', 'PENDIENTE'])

    const misReportes: FocoData[] = []
    const comunidad: FocoData[] = []

    for (const f of focos) {
      if (misIdSet.has(f.id)) {
        misReportes.push(f)
        continue
      }
      if (!VALID_ESTADOS.has(f.estado.toUpperCase())) continue
      if (haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], f.lat, f.lng) > RADIO_MAX_KM) continue
      const t = new Date(f.created_at).getTime()
      if (isNaN(t) || t < corte) continue
      comunidad.push(f)
    }

    comunidad.sort((a, b) => {
      const dA = haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], a.lat, a.lng)
      const dB = haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], b.lat, b.lng)
      return dA - dB
    })

    const resultado = comunidad.slice(0, 5)
    const idsEnResultado = new Set(resultado.map(f => f.id))

    for (const f of misReportes) {
      if (!idsEnResultado.has(f.id)) {
        resultado.push(f)
        idsEnResultado.add(f.id)
      }
    }

    if (highlightId && !idsEnResultado.has(highlightId)) {
      const highlight = focos.find(f => f.id === highlightId)
      if (highlight) resultado.push(highlight)
    }

    return resultado
  }, [focos, highlightId, misIds])

  const toggleStrategy = () => {
    setStrategyIdx((prev) => (prev + 1) % strategies.length)
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <div className="bg-fire-500 text-white p-4 shrink-0 flex justify-between items-start">
        <div>
          <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
          <p className="text-sm opacity-90">{loading ? 'Cargando...' : `${focosFiltrados.length} focos cercanos`}</p>
        </div>
        <div className="flex items-center gap-2">
          {strategies.length > 1 && (
            <button
              onClick={toggleStrategy}
              className="bg-white/20 hover:bg-white/30 rounded px-2 py-1 text-xs transition-colors"
            >
              {strategy.label}
            </button>
          )}
          <div className="bg-white/20 rounded-full px-2.5 py-1 text-xs whitespace-nowrap">
            Slots: {misReportesCount}/5
          </div>
        </div>
      </div>

      <div className="flex-1 relative min-h-0">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-20">
            <div className="text-center max-w-xs">
              <span className="text-4xl inline-block mb-2">⚠️</span>
              <p className="text-red-600 text-sm font-medium">Error</p>
              <p className="text-gray-600 text-xs mt-1">{error}</p>
              <button onClick={handleRetry} className="mt-3 px-4 py-1.5 bg-fire-500 text-white text-sm rounded hover:bg-fire-600">
                Reintentar
              </button>
            </div>
          </div>
        )}

        {loading && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-fire-500 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">Cargando focos...</p>
            </div>
          </div>
        )}

        <div className="relative w-full h-[calc(100vh-280px)] md:h-[calc(100vh-180px)] z-0">
          {strategy.renderMap({
            focos: focosFiltrados,
            highlightId,
            centerTo,
            selectedFoco,
            onSelectFoco: setSelectedFoco,
            onMapReady: handleMapReady,
          })}
        </div>

        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
          <h3 className="text-xs font-semibold mb-1">Leyenda:</h3>
          {['ACTIVO', 'PENDIENTE', 'CONTROLADO', 'EXTINGUIDO'].map((estado) => (
            <div key={estado} className="flex items-center gap-2 mt-1">
              <span className="w-3 h-3 rounded-full" style={{ backgroundColor: estadoDot(estado) }} />
              <span className="text-xs">{estado.charAt(0) + estado.slice(1).toLowerCase()}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white p-4 border-t shrink-0 max-h-48 overflow-y-auto">
        <h3 className="font-semibold mb-3">Focos Recientes:</h3>
        {focosFiltrados.length === 0 && !loading ? (
          <p className="text-sm text-gray-500 text-center py-4">No hay focos activos cercanos</p>
        ) : (
          <div className="space-y-2">
            {focosFiltrados.map((foco) => (
              <div
                key={foco.id}
                onClick={() => flyToFoco(foco)}
                className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                  foco.id === highlightId ? 'bg-blue-50 ring-2 ring-blue-400' : 'bg-gray-50 hover:bg-gray-100'
                }`}
              >
                {foco.foto_url ? (
                  <img
                    src={foco.foto_url}
                    alt=""
                    className="w-10 h-10 rounded object-cover shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ) : (
                  <div className="w-10 h-10 rounded bg-gray-200 shrink-0 flex items-center justify-center">
                    <MapPin className="w-5 h-5 text-gray-400" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">
                    <span className="inline-block w-2.5 h-2.5 rounded-full mr-1" style={{ backgroundColor: estadoDot(foco.estado) }} />
                    {tipoLabel(foco.tipo)}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {foco.lat.toFixed(4)}, {foco.lng.toFixed(4)}
                    {foco.descripcion && ` — ${foco.descripcion.slice(0, 40)}${foco.descripcion.length > 40 ? '…' : ''}`}
                  </p>
                </div>
                <span className={`ml-auto px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${estadoColor(foco.estado)}`}>
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

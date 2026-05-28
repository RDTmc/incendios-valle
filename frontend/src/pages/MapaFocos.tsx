import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import Map, { Marker, Popup, GeolocateControl, useMap } from 'react-map-gl/mapbox'
import type { MapRef } from 'react-map-gl/mapbox'
import 'mapbox-gl/dist/mapbox-gl.css'
import { useLocation } from 'react-router-dom'
import { MapPin } from 'lucide-react'
import { API } from '../api'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN
const VALLE_DEL_SOL: [number, number] = [-33.4489, -70.6693]
const RADIO_MAX_KM = 50

function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

interface FocoActivo {
  id: string
  lat: number
  lng: number
  estado: string
  tipo: string
  descripcion?: string
  foto_url?: string
  created_at: string
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

const estadoDot = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return '#dc2626'
    case 'PENDIENTE':  return '#d97706'
    case 'CONTROLADO': return '#f97316'
    case 'EXTINGUIDO': return '#16a34a'
    default:           return '#9ca3af'
  }
}

const tipoLabel = (tipo: string) =>
  tipo.toLowerCase() === 'forestal' ? 'Forestal' : 'Urbano'

function FlyToCenter({ target }: { target: [number, number] | null }) {
  const { current: map } = useMap()
  useEffect(() => {
    if (target && map) {
      map.flyTo({ center: [target[1], target[0]], zoom: 14, duration: 1500 })
    }
  }, [map, target])
  return null
}

function FocoMarker({ foco, highlight, onClick }: { foco: FocoActivo; highlight: boolean; onClick: () => void }) {
  if (highlight && foco.foto_url) {
    return (
      <Marker longitude={foco.lng} latitude={foco.lat} anchor="bottom" onClick={onClick}>
        <div className="relative" style={{ cursor: 'pointer' }}>
          <div className="absolute -inset-3 rounded-full bg-blue-500/30 animate-ping" />
          <div className="relative w-14 h-14 rounded-full ring-4 ring-blue-500 shadow-lg overflow-hidden bg-white">
            <img src={foco.foto_url} alt="" className="w-full h-full object-cover" />
          </div>
        </div>
      </Marker>
    )
  }
  const color = estadoDot(foco.estado)
  const size = highlight ? 44 : 32
  return (
    <Marker longitude={foco.lng} latitude={foco.lat} anchor="bottom" onClick={onClick}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: size,
          height: size,
          background: color,
          borderRadius: '50%',
          border: highlight ? '4px solid #fff' : '3px solid #fff',
          boxShadow: highlight
            ? '0 0 0 3px rgba(37,99,235,0.5), 0 2px 6px rgba(0,0,0,0.3)'
            : '0 2px 6px rgba(0,0,0,0.3)',
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width={highlight ? 20 : 16} height={highlight ? 20 : 16}>
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
        </svg>
      </div>
    </Marker>
  )
}

export default function MapaFocos() {
  const location = useLocation()
  const state = location.state as { centerTo?: [number, number]; highlightId?: string } | null
  const centerTo = state?.centerTo ?? null
  const highlightId = state?.highlightId ?? null

  const mapRef = useRef<MapRef>(null)
  const [focos, setFocos] = useState<FocoActivo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFoco, setSelectedFoco] = useState<FocoActivo | null>(null)

  useEffect(() => {
    const ab = new AbortController()
    setLoading(true)
    setError(null)
    API.getFocosActivos()
      .then((data: FocoActivo[]) => {
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

  const handleRetry = () => {
    setLoading(true)
    setError(null)
    API.getFocosActivos()
      .then((data: FocoActivo[]) => setFocos(data))
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false))
  }

  const flyToFoco = useCallback((foco: FocoActivo) => {
    if (mapRef.current) {
      mapRef.current.flyTo({ center: [foco.lng, foco.lat], zoom: 14, duration: 1000 })
    }
  }, [])

  const focosFiltrados = useMemo(() => {
    const candidatos = focos
      .filter(f => { const e = f.estado.toUpperCase(); return e === 'ACTIVO' || e === 'PENDIENTE' })
      .filter(f => haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], f.lat, f.lng) <= RADIO_MAX_KM)
      .sort((a, b) => {
        const dA = haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], a.lat, a.lng)
        const dB = haversineKm(VALLE_DEL_SOL[0], VALLE_DEL_SOL[1], b.lat, b.lng)
        return dA - dB
      })

    const top5 = candidatos.slice(0, 5)

    if (highlightId) {
      const highlight = candidatos.find(f => f.id === highlightId)
      if (highlight && !top5.some(f => f.id === highlightId)) {
        top5.push(highlight)
      }
    }

    return top5
  }, [focos, highlightId])

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <div className="bg-fire-500 text-white p-4 shrink-0">
        <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
        <p className="text-sm opacity-90">{loading ? 'Cargando...' : `${focosFiltrados.length} focos cercanos`}</p>
      </div>

      <div className="flex-1 relative min-h-0">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-20">
            <div className="text-center max-w-xs">
              <span className="text-4xl inline-block mb-2">⚠️</span>
              <p className="text-red-600 text-sm font-medium">Error</p>
              <p className="text-gray-600 text-xs mt-1">{error}</p>
              <button
                onClick={handleRetry}
                className="mt-3 px-4 py-1.5 bg-fire-500 text-white text-sm rounded hover:bg-fire-600"
              >
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
        <Map
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          style={{ width: '100%', height: '100%' }}
          mapStyle="mapbox://styles/mapbox/streets-v12"
          initialViewState={{
            latitude: centerTo ? centerTo[0] : VALLE_DEL_SOL[0],
            longitude: centerTo ? centerTo[1] : VALLE_DEL_SOL[1],
            zoom: centerTo ? 14 : 12
          }}
          onClick={() => setSelectedFoco(null)}
        >
          <GeolocateControl position="top-right" trackUserLocation />

          <FlyToCenter target={centerTo} />

          {focosFiltrados.map((foco) => (
            <FocoMarker
              key={foco.id}
              foco={foco}
              highlight={foco.id === highlightId}
              onClick={() => setSelectedFoco(foco)}
            />
          ))}

          {selectedFoco && (
            <Popup
              longitude={selectedFoco.lng}
              latitude={selectedFoco.lat}
              anchor="bottom"
              onClose={() => setSelectedFoco(null)}
              closeButton={true}
              closeOnClick={false}
              offset={[0, -8]}
            >
              <div className="min-w-[180px] text-sm">
                <p className="font-semibold text-base mb-1">{tipoLabel(selectedFoco.tipo)}</p>
                {selectedFoco.descripcion && (
                  <p className="text-gray-700 mb-1 leading-tight">{selectedFoco.descripcion}</p>
                )}
                {selectedFoco.foto_url && (
                  <img
                    src={selectedFoco.foto_url}
                    alt="Foto del incendio"
                    className="w-full h-28 object-cover rounded mt-1"
                    loading="lazy"
                  />
                )}
                <span className={`inline-block mt-1.5 px-2 py-0.5 rounded text-xs font-medium ${estadoColor(selectedFoco.estado)}`}>
                  {selectedFoco.estado}
                </span>
              </div>
            </Popup>
          )}
        </Map>
        </div>

        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
          <h3 className="text-xs font-semibold mb-1">Leyenda:</h3>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#dc2626' }} />
            <span className="text-xs">Activo</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: '#d97706' }} />
            <span className="text-xs">Pendiente</span>
          </div>
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
                  foco.id === highlightId
                    ? 'bg-blue-50 ring-2 ring-blue-400'
                    : 'bg-gray-50 hover:bg-gray-100'
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
                    <span
                      className="inline-block w-2.5 h-2.5 rounded-full mr-1"
                      style={{ backgroundColor: estadoDot(foco.estado) }}
                    />
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

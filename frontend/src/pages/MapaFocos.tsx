import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import { API } from '../api'

const VALLE_DEL_SOL: [number, number] = [-33.4489, -70.6693]

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
    case 'CONTROLADO': return 'bg-orange-100 text-orange-700'
    case 'EXTINGUIDO': return 'bg-green-100 text-green-700'
    default:           return 'bg-gray-100 text-gray-700'
  }
}

const estadoDot = (estado: string) => {
  switch (estado.toUpperCase()) {
    case 'ACTIVO':     return '#dc2626'
    case 'CONTROLADO': return '#f97316'
    case 'EXTINGUIDO': return '#16a34a'
    default:           return '#9ca3af'
  }
}

const tipoLabel = (tipo: string) =>
  tipo.toLowerCase() === 'forestal' ? 'Forestal' : 'Urbano'

function createMarkerIcon(color: string) {
  return L.divIcon({
    className: '',
    html: `<div style="display:flex;align-items:center;justify-content:center;width:32px;height:32px;background:${color};border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="16" height="16"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -36]
  })
}

function LocationUpdater({ onCenter }: { onCenter: (lat: number, lng: number) => void }) {
  const map = useMap()
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords
          map.setView([latitude, longitude], 13)
          onCenter(latitude, longitude)
        },
        () => {},
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      )
    }
  }, [map, onCenter])
  return null
}

export default function MapaFocos() {
  const [focos, setFocos] = useState<FocoActivo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [mapCenter, setMapCenter] = useState<[number, number]>(VALLE_DEL_SOL)

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

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <div className="bg-fire-500 text-white p-4 shrink-0">
        <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
        <p className="text-sm opacity-90">{loading ? 'Cargando...' : `${focos.length} focos en tiempo real`}</p>
      </div>

      <div className="flex-1 relative">
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

        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-fire-500 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">Cargando focos...</p>
            </div>
          </div>
        )}

        <MapContainer
          center={mapCenter}
          zoom={12}
          className="w-full h-full"
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <LocationUpdater onCenter={(lat, lng) => setMapCenter([lat, lng])} />
          {focos.map((foco) => (
            <Marker
              key={foco.id}
              position={[foco.lat, foco.lng]}
              icon={createMarkerIcon(estadoDot(foco.estado))}
            >
              <Popup>
                <div className="min-w-[180px] text-sm">
                  <p className="font-semibold text-base mb-1">{tipoLabel(foco.tipo)}</p>
                  {foco.descripcion && (
                    <p className="text-gray-700 mb-1 leading-tight">{foco.descripcion}</p>
                  )}
                  {foco.foto_url && (
                    <img
                      src={foco.foto_url}
                      alt="Foto del incendio"
                      className="w-full h-28 object-cover rounded mt-1"
                      loading="lazy"
                    />
                  )}
                  <span className={`inline-block mt-1.5 px-2 py-0.5 rounded text-xs font-medium ${estadoColor(foco.estado)}`}>
                    {foco.estado}
                  </span>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-[1000]">
          <h3 className="text-sm font-semibold mb-2">Leyenda:</h3>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#dc2626' }} />
              <span className="text-xs">Activo</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#f97316' }} />
              <span className="text-xs">Controlado</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-4 h-4 rounded-full" style={{ backgroundColor: '#16a34a' }} />
              <span className="text-xs">Extinguido</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white p-4 border-t shrink-0 max-h-48 overflow-y-auto">
        <h3 className="font-semibold mb-3">Focos Recientes:</h3>
        {focos.length === 0 && !loading ? (
          <p className="text-sm text-gray-500 text-center py-4">No hay focos registrados</p>
        ) : (
          <div className="space-y-2">
            {focos.map((foco) => (
              <div
                key={foco.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">
                    <span className="inline-block w-2.5 h-2.5 rounded-full mr-2" style={{ backgroundColor: estadoDot(foco.estado) }} />
                    {tipoLabel(foco.tipo)}
                  </p>
                  <p className="text-xs text-gray-500 truncate">
                    {foco.lat.toFixed(4)}, {foco.lng.toFixed(4)}
                    {foco.descripcion && ` — ${foco.descripcion.slice(0, 40)}${foco.descripcion.length > 40 ? '…' : ''}`}
                  </p>
                </div>
                <span className={`ml-2 px-2 py-1 rounded text-xs font-medium whitespace-nowrap ${estadoColor(foco.estado)}`}>
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

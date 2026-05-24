import { useState, useEffect, useCallback, useRef } from 'react'
import { useJsApiLoader, GoogleMap, Marker, InfoWindow } from '@react-google-maps/api'
import { API } from '../api'

const VALLE_DEL_SOL = { lat: -33.4489, lng: -70.6693 }

const containerStyle = {
  width: '100%',
  height: '100%'
}

const DEFAULT_ZOOM = 12

// P3-4: Google Maps integration for tactical fire visualization

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
    case 'ACTIVO':     return 'bg-red-500'
    case 'CONTROLADO': return 'bg-orange-500'
    case 'EXTINGUIDO': return 'bg-green-500'
    default:           return 'bg-gray-400'
  }
}

const markerIcon = (estado: string) => {
  const color = (() => {
    switch (estado.toUpperCase()) {
      case 'ACTIVO':     return 'db3622'
      case 'CONTROLADO': return 'f57c00'
      case 'EXTINGUIDO': return '2e7d32'
      default:           return '9e9e9e'
    }
  })()
  return {
    url: `https://maps.google.com/mapfiles/ms/icons/${color}-dot.png`,
    scaledSize: new google.maps.Size(36, 36),
    origin: new google.maps.Point(0, 0),
    anchor: new google.maps.Point(18, 36)
  }
}

const tipoLabel = (tipo: string) =>
  tipo.toLowerCase() === 'forestal' ? '🌲 Forestal' : '🏠 Urbano'

export default function MapaFocos() {
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''

  const { isLoaded, loadError } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: apiKey
  })

  const [focos, setFocos] = useState<FocoActivo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<FocoActivo | null>(null)
  const [userLocation, setUserLocation] = useState<google.maps.LatLngLiteral | null>(null)
  const mapRef = useRef<google.maps.Map | null>(null)

  const onLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map
  }, [])

  const onUnmount = useCallback(() => {
    mapRef.current = null
  }, [])

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

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude
        }),
        () => {}
      )
    }
  }, [])

  if (loadError) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center max-w-xs">
          <span className="text-4xl">⚠️</span>
          <p className="text-red-600 mt-2 text-sm font-medium">Error al cargar Google Maps</p>
          <p className="text-gray-600 text-xs mt-1">Verifica que VITE_GOOGLE_MAPS_API_KEY esté configurada</p>
        </div>
      </div>
    )
  }

  const mapCenter = userLocation || VALLE_DEL_SOL

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <div className="bg-fire-500 text-white p-4">
        <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
        <p className="text-sm opacity-90">{loading ? 'Cargando...' : `${focos.length} focos en tiempo real`}</p>
      </div>

      <div className="flex-1 relative">
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-fire-500 mx-auto mb-3" />
              <p className="text-gray-600 text-sm">Cargando mapa...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/50 z-10">
            <div className="text-center max-w-xs">
              <span className="text-4xl">⚠️</span>
              <p className="text-red-600 mt-2 text-sm font-medium">Error</p>
              <p className="text-gray-600 text-xs mt-1">{error}</p>
              <button
                onClick={() => {
                  setLoading(true)
                  setError(null)
                  API.getFocosActivos()
                    .then((data: FocoActivo[]) => setFocos(data))
                    .catch((err: Error) => setError(err.message))
                    .finally(() => setLoading(false))
                }}
                className="mt-3 px-4 py-1.5 bg-fire-500 text-white text-sm rounded hover:bg-fire-600"
              >
                Reintentar
              </button>
            </div>
          </div>
        )}

        {isLoaded && (
          <GoogleMap
            mapContainerStyle={containerStyle}
            center={mapCenter}
            zoom={DEFAULT_ZOOM}
            onLoad={onLoad}
            onUnmount={onUnmount}
            options={{
              mapTypeControl: true,
              streetViewControl: false,
              fullscreenControl: false,
              zoomControl: true
            }}
          >
            {focos.map((foco) => (
              <Marker
                key={foco.id}
                position={{ lat: foco.lat, lng: foco.lng }}
                icon={markerIcon(foco.estado)}
                onClick={() => setSelected(foco)}
              />
            ))}

            {selected && (
              <InfoWindow
                position={{ lat: selected.lat, lng: selected.lng }}
                onCloseClick={() => setSelected(null)}
              >
                <div className="max-w-[220px] text-sm" style={{ fontFamily: 'system-ui, sans-serif' }}>
                  <p className="font-semibold text-base mb-1">
                    {tipoLabel(selected.tipo)}
                  </p>
                  {selected.descripcion && (
                    <p className="text-gray-700 mb-1 leading-tight">{selected.descripcion}</p>
                  )}
                  {selected.foto_url && (
                    <img
                      src={selected.foto_url}
                      alt="Foto del incendio"
                      className="w-full h-28 object-cover rounded mt-1"
                      loading="lazy"
                    />
                  )}
                  <span className={`inline-block mt-1.5 px-2 py-0.5 rounded text-xs font-medium ${estadoColor(selected.estado)}`}>
                    {selected.estado}
                  </span>
                </div>
              </InfoWindow>
            )}
          </GoogleMap>
        )}

        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3 z-10">
          <h3 className="text-sm font-semibold mb-2">Leyenda:</h3>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <img src="https://maps.google.com/mapfiles/ms/icons/red-dot.png" className="w-5 h-5" alt="" />
              <span className="text-xs">Activo</span>
            </div>
            <div className="flex items-center gap-2">
              <img src="https://maps.google.com/mapfiles/ms/icons/orange-dot.png" className="w-5 h-5" alt="" />
              <span className="text-xs">Controlado</span>
            </div>
            <div className="flex items-center gap-2">
              <img src="https://maps.google.com/mapfiles/ms/icons/green-dot.png" className="w-5 h-5" alt="" />
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
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {focos.map((foco) => (
              <div
                key={foco.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
                onClick={() => {
                  setSelected(foco)
                  if (mapRef.current) {
                    mapRef.current.panTo({ lat: foco.lat, lng: foco.lng })
                    mapRef.current.setZoom(15)
                  }
                }}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm truncate">
                    <span className={`inline-block w-2.5 h-2.5 rounded-full ${estadoDot(foco.estado)} mr-2`} />
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

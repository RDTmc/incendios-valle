import { useNavigate, useLocation } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'

function createUserMarkerIcon() {
  return L.divIcon({
    className: '',
    html: '<div style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#2563eb;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="14" height="14"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>',
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  })
}

function MapPreview({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView([lat, lng], 15, { animate: true })
    setTimeout(() => map.invalidateSize(), 200)
  }, [map, lat, lng])
  return null
}

export default function Confirmacion() {
  const navigate = useNavigate()
  const location = useLocation()
  const data = location.state as {
    reporte: { report_id: string; estado: string; created_at: string }
    lat: number
    lng: number
    tipo: string
    fotoUrl?: string
  } | null

  const reportId = data?.reporte?.report_id ?? '---'
  const lat = data?.lat ?? 0
  const lng = data?.lng ?? 0
  const tipo = data?.tipo ?? 'FORESTAL'
  const createdAt = data?.reporte?.created_at ?? ''
  const fotoUrl = data?.fotoUrl ?? ''

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-lg mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Estado */}
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white text-2xl">✓</span>
            </div>
            <h1 className="text-xl font-bold text-gray-800">Reporte Enviado</h1>
            <p className="text-gray-500">ID: {reportId}</p>
          </div>

          {/* Mapa de previsualización */}
          <div className="rounded-lg overflow-hidden border border-gray-200 h-64 mb-6 w-full">
            <MapContainer
              center={[lat, lng]}
              zoom={15}
              className="w-full h-full"
              zoomControl={false}
              dragging={false}
              scrollWheelZoom={false}
              doubleClickZoom={false}
              touchZoom={false}
              keyboard={false}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapPreview lat={lat} lng={lng} />
              <Marker position={[lat, lng]} icon={createUserMarkerIcon()} />
            </MapContainer>
          </div>

          {/* Foto subida */}
          {fotoUrl && (
            <div className="mb-6">
              <img
                src={fotoUrl}
                alt="Foto del incendio"
                className="w-full rounded-lg shadow-md object-cover max-h-64"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            </div>
          )}

          {/* Detalles */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h3 className="font-semibold text-gray-700 mb-2">Detalles del Reporte:</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>📍 Latitud: {lat.toFixed(6)}</li>
              <li>📍 Longitud: {lng.toFixed(6)}</li>
              <li>🔥 Tipo: {tipo === 'FORESTAL' ? 'Forestal' : 'Urbano'}</li>
              <li>⏰ Estado: {data?.reporte?.estado ?? 'Pendiente de validación'}</li>
              {createdAt && <li>🕐 Creado: {new Date(createdAt).toLocaleString('es-CL')}</li>}
            </ul>
          </div>

          {/* Botones */}
          <div className="space-y-3">
            <button
              onClick={() => navigate('/reporte')}
              className="w-full bg-fire-500 hover:bg-fire-600 text-white font-semibold py-3 rounded-lg"
            >
              Nuevo Reporte
            </button>
            <button
              onClick={() => navigate('/mapa', {
                state: { centerTo: [lat, lng], highlightId: reportId }
              })}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 rounded-lg"
            >
              Ver Mapa de Focos
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
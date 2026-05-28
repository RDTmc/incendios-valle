import { useNavigate, useLocation } from 'react-router-dom'

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

          {/* Mapa simulado */}
          <div className="bg-gray-200 rounded-lg h-64 mb-6 flex items-center justify-center">
            <div className="text-center">
              <span className="text-4xl">🗺️</span>
              <p className="text-gray-600 mt-2">
                Ubicación: {lat.toFixed(4)}, {lng.toFixed(4)}
              </p>
              <p className="text-xs text-gray-500">(Mapa de Google)</p>
            </div>
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
import { useState, useEffect } from 'react'
import { useAuth } from '../App'
import { API } from '../api'
import { useNavigate, useLocation } from 'react-router-dom'

interface Reporte {
  report_id: string
  tipo: string
  estado: string
  created_at: string
  latitud: string
  longitud: string
  descripcion: string
}

function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const path = location.pathname

  const tabs = [
    { path: '/historial', label: 'Historial', icon: '📋' },
    { path: '/mapa', label: 'Mapa', icon: '🗺️' },
    { path: '/reporte', label: 'Reportar', icon: '➕' },
  ]

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-2">
      <div className="flex justify-around">
        {tabs.map(tab => (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`flex flex-col items-center px-4 py-1 rounded-lg transition-colors ${
              path === tab.path ? 'text-fire-500 bg-fire-50 font-medium' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <span className="text-lg">{tab.icon}</span>
            <span className="text-xs">{tab.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default function Historial() {
  const { user, token, logout } = useAuth()
  const navigate = useNavigate()
  const [reportes, setReportes] = useState<Reporte[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token && user) {
      API.getReports(token, user.user_id)
        .then(data => setReportes(data))
        .catch(err => console.error('Error:', err))
        .finally(() => setLoading(false))
    }
  }, [token, user])

  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'VALIDADO': return 'bg-green-100 text-green-700'
      case 'CONTROLADO': return 'bg-blue-100 text-blue-700'
      case 'PENDIENTE': return 'bg-yellow-100 text-yellow-700'
      case 'RECHAZADO': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString('es-CL')
    } catch {
      return dateStr
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 pb-20">
      <div className="bg-white p-4 shadow flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-800">Mis Reportes</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600 truncate max-w-[120px]">{user?.nombre || user?.email}</span>
          <button
            onClick={() => { logout(); navigate('/login') }}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Cerrar Sesión
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Cargando...</p>
          </div>
        ) : reportes.length === 0 ? (
          <div className="text-center py-8">
            <span className="text-4xl">📋</span>
            <p className="text-gray-500 mt-2">No tienes reportes aún</p>
            <button
              onClick={() => navigate('/reporte')}
              className="mt-3 text-fire-500 hover:underline text-sm"
            >
              Reportar un incendio
            </button>
          </div>
        ) : (
          reportes.map((reporte) => (
            <div key={reporte.report_id} className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="font-semibold text-gray-800 text-sm">Reporte #{reporte.report_id.slice(0, 8)}</h3>
                  <p className="text-xs text-gray-500">{formatDate(reporte.created_at)}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${getEstadoColor(reporte.estado)}`}>
                  {reporte.estado}
                </span>
              </div>
              
              <div className="flex items-center gap-2 mt-2">
                <span className="text-lg">
                  {reporte.tipo === 'FORESTAL' ? '🌲' : '🏠'}
                </span>
                <span className="text-sm text-gray-600">
                  Incendio {reporte.tipo.toLowerCase()}
                </span>
                <span className="text-xs text-gray-400 ml-auto">
                  {reporte.latitud}, {reporte.longitud}
                </span>
              </div>

              {reporte.descripcion && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">{reporte.descripcion}</p>
              )}

              <button
                onClick={() => navigate('/mapa', { state: { lat: parseFloat(reporte.latitud), lng: parseFloat(reporte.longitud), reportId: reporte.report_id } })}
                className="mt-3 text-sm text-fire-500 hover:underline"
              >
                Ver en mapa →
              </button>
            </div>
          ))
        )}
      </div>

      <BottomNav />
    </div>
  )
}

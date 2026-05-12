import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../App'
import { API } from '../api'

interface ReporteData {
  tipo: 'FORESTAL' | 'URBANO'
  lat: number | null
  lng: number | null
  descripcion: string
  foto: File | null
}

export default function Reporte() {
  const navigate = useNavigate()
  const { user, token } = useAuth()
  const [reporte, setReporte] = useState<ReporteData>({
    tipo: 'FORESTAL',
    lat: null,
    lng: null,
    descripcion: '',
    foto: null
  })
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const getLocation = () => {
    if (navigator.geolocation) {
      setLoading(true)
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setReporte({
            ...reporte,
            lat: position.coords.latitude,
            lng: position.coords.longitude
          })
          setLoading(false)
        },
        (error) => {
          console.error('Error getting location:', error)
          setLoading(false)
        }
      )
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reporte.lat || !reporte.lng) {
      alert('Por favor obtén tu ubicación primero')
      return
    }
    if (!token || !user) {
      alert('Sesión expirada. Inicia sesión de nuevo.')
      navigate('/login')
      return
    }
    setSubmitting(true)
    try {
      await API.createReport(token, {
        user_id: user.user_id,
        tipo: reporte.tipo,
        latitud: reporte.lat,
        longitud: reporte.lng,
        descripcion: reporte.descripcion
      })
      navigate('/confirmar')
    } catch (err: any) {
      console.error('Error al enviar:', err)
      alert(err.message || 'Error al enviar reporte. Intenta de nuevo.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setReporte({ ...reporte, foto: e.target.files[0] })
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-lg mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-xl font-bold text-gray-800 mb-6">Reportar Incendio</h1>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Tipo de incendio */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Incendio
              </label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => setReporte({ ...reporte, tipo: 'FORESTAL' })}
                  className={`p-3 rounded-lg border-2 ${
                    reporte.tipo === 'FORESTAL' 
                      ? 'border-fire-500 bg-fire-50' 
                      : 'border-gray-200'
                  }`}
                >
                  🌲 Forestal
                </button>
                <button
                  type="button"
                  onClick={() => setReporte({ ...reporte, tipo: 'URBANO' })}
                  className={`p-3 rounded-lg border-2 ${
                    reporte.tipo === 'URBANO' 
                      ? 'border-fire-500 bg-fire-50' 
                      : 'border-gray-200'
                  }`}
                >
                  🏠 Urbano
                </button>
              </div>
            </div>

            {/* Ubicación */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Ubicación
              </label>
              <button
                type="button"
                onClick={getLocation}
                disabled={loading}
                className="w-full py-3 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? 'Obteniendo ubicación...' : '📍 Obtener Mi Ubicación'}
              </button>
              {reporte.lat && reporte.lng && (
                <p className="mt-2 text-sm text-green-600">
                  ✅ Ubicación: {reporte.lat.toFixed(4)}, {reporte.lng.toFixed(4)}
                </p>
              )}
            </div>

            {/* Cámara / Foto */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fotografía
              </label>
              <label className="w-full py-3 px-4 border-2 border-dashed border-gray-300 rounded-lg block text-center cursor-pointer hover:border-fire-500">
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileChange}
                  className="hidden"
                />
                {reporte.foto ? (
                  <span className="text-green-600">📷 {reporte.foto.name}</span>
                ) : (
                  <span className="text-gray-500">📷 Tomar foto</span>
                )}
              </label>
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descripción (opcional)
              </label>
              <textarea
                value={reporte.descripcion}
                onChange={(e) => setReporte({ ...reporte, descripcion: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 bg-gray-900 text-white placeholder-gray-400"
                placeholder="Describe lo que observas..."
                rows={3}
              />
            </div>

            {/* Botón enviar */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-fire-500 hover:bg-fire-600 text-white font-semibold py-3 rounded-lg disabled:opacity-50"
            >
              {submitting ? 'Enviando...' : 'Enviar Reporte'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trees, Home, MapPin, Camera, ShieldCheck, Flame } from 'lucide-react'
import { useAuth } from '../App'
import { API } from '../api'
import { compressImage } from '../util/image'
import { getDeviceId } from '../util/device'

interface ReporteData {
  tipo: 'FORESTAL' | 'URBANO'
  lat: number | null
  lng: number | null
  descripcion: string
  fotoUrl: string
  fotoName: string
}

export default function Reporte() {
  const navigate = useNavigate()
  const { user, token, logout } = useAuth()
  const isAnonymous = !token || !user
  const [reporte, setReporte] = useState<ReporteData>({
    tipo: 'FORESTAL',
    lat: null,
    lng: null,
    descripcion: '',
    fotoUrl: '',
    fotoName: ''
  })
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
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
    setSubmitting(true)
    try {
      const payload: any = {
        tipo: reporte.tipo,
        latitud: reporte.lat,
        longitud: reporte.lng,
        descripcion: reporte.descripcion
      }
      if (reporte.fotoUrl) {
        payload.foto_url = reporte.fotoUrl
      }

      let result: any
      if (isAnonymous) {
        payload.device_id = getDeviceId()
        result = await API.createReportAnonimo(payload)
      } else {
        payload.user_id = user!.user_id
        result = await API.createReport(token!, payload)
      }

      navigate('/confirmar', { state: { reporte: result, lat: reporte.lat, lng: reporte.lng, tipo: reporte.tipo, fotoUrl: reporte.fotoUrl, isAnonymous } })
    } catch (err: any) {
      console.error('Error al enviar:', err)
      alert(err.message || 'Error al enviar reporte. Intenta de nuevo.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const compressed = await compressImage(file)
      const optimized = new File([compressed], file.name.replace(/\.[^.]+$/, '.jpg'), { type: 'image/jpeg' })
      const url = await API.uploadImage(optimized)
      setReporte({ ...reporte, fotoUrl: url, fotoName: file.name })
    } catch (err: any) {
      alert(err.message || 'Error al subir imagen. Intenta de nuevo.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="h-screen overflow-hidden bg-gray-100">
      <div className="h-full flex flex-col max-w-lg mx-auto">

        {/* Cabecera institucional roja */}
        <div className="bg-fire-500 text-center text-white shrink-0">
          <div className="w-full flex justify-center py-3">
            <img
              src="/logo-muni.png"
              alt="Municipalidad de Valle del Sol"
              className="h-44 md:h-52 w-auto object-contain brightness-0 invert"
            />
          </div>
          <h1 className="text-lg font-bold pb-3">Reportar Incendio</h1>
        </div>

        <div className="p-4 flex-1 min-h-0 overflow-y-auto">
          {/* Indicador de estado */}
          {isAnonymous ? (
            <div className="bg-orange-100 border-l-4 border-orange-500 text-orange-800 p-2 mb-2 rounded text-xs font-medium flex items-center gap-2">
              <Flame className="w-4 h-4 shrink-0 animate-pulse" />
              <span>Reporte de Emergencia Rápido</span>
              <span className="text-[10px] font-normal opacity-70 ml-auto">Anónimo</span>
            </div>
          ) : (
            <div className="bg-green-100 border-l-4 border-green-500 text-green-800 p-2 mb-2 rounded text-xs font-medium flex items-center justify-between">
              <span className="flex items-center gap-1 truncate"><ShieldCheck className="w-4 h-4 text-green-600 shrink-0" /> {user?.nombre || user?.email}</span>
              <button
                onClick={() => { logout(); navigate('/login') }}
                className="text-xs text-red-600 hover:text-red-800 font-medium ml-2 shrink-0"
              >
                Cerrar
              </button>
            </div>
          )}

          <div className="bg-white rounded-lg shadow-lg p-4">

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Tipo de incendio */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Tipo de Incendio
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setReporte({ ...reporte, tipo: 'FORESTAL' })}
                  className={`p-2 rounded-lg border-2 text-sm ${
                    reporte.tipo === 'FORESTAL' 
                      ? 'border-fire-500 bg-fire-50' 
                      : 'border-gray-200'
                  }`}
                >
                  <Trees className="w-4 h-4 inline-block mr-1" />
                  Forestal
                </button>
                <button
                  type="button"
                  onClick={() => setReporte({ ...reporte, tipo: 'URBANO' })}
                  className={`p-2 rounded-lg border-2 text-sm ${
                    reporte.tipo === 'URBANO' 
                      ? 'border-fire-500 bg-fire-50' 
                      : 'border-gray-200'
                  }`}
                >
                  <Home className="w-4 h-4 inline-block mr-1" />
                  Urbano
                </button>
              </div>
            </div>

            {/* Ubicación */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Ubicación
              </label>
              <button
                type="button"
                onClick={getLocation}
                disabled={loading}
                className="w-full py-2 px-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 text-sm"
              >
                {loading ? 'Obteniendo ubicación...' : <><MapPin className="w-4 h-4 inline-block mr-1" /> Obtener Mi Ubicación</>}
              </button>
              {reporte.lat && reporte.lng && (
                <p className="mt-1 text-xs text-green-600">
                  ✅ Ubicación: {reporte.lat.toFixed(4)}, {reporte.lng.toFixed(4)}
                </p>
              )}
            </div>

            {/* Cámara / Foto */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Fotografía
              </label>
              <label className="w-full py-2 px-3 border-2 border-dashed border-gray-300 rounded-lg block text-center cursor-pointer hover:border-fire-500 text-sm">
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileChange}
                  disabled={uploading}
                  className="hidden"
                />
                {uploading ? (
                  <span className="text-blue-600">⏳ Subiendo...</span>
                ) : reporte.fotoUrl ? (
                  <span className="text-green-600">✅ {reporte.fotoName}</span>
                ) : (
                  <span className="text-gray-500"><Camera className="w-4 h-4 inline-block mr-1" /> Tomar foto</span>
                )}
              </label>
            </div>

            {/* Descripción */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Descripción (opcional)
              </label>
              <textarea
                value={reporte.descripcion}
                onChange={(e) => setReporte({ ...reporte, descripcion: e.target.value })}
                className="w-full px-3 py-1.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 bg-gray-900 text-white placeholder-gray-400 text-sm"
                placeholder="Describe lo que observas..."
                rows={2}
              />
            </div>

            {/* Botón enviar */}
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-fire-500 hover:bg-fire-600 text-white font-semibold py-2 rounded-lg disabled:opacity-50 text-sm"
            >
              {submitting ? 'Enviando...' : 'Enviar Reporte'}
            </button>
          </form>
        </div>

        {isAnonymous && (
          <div className="mt-2 text-center">
            <button
              onClick={() => navigate('/login')}
              className="text-xs text-fire-500 hover:underline"
            >
              ¿Ya tienes cuenta? Inicia sesión aquí
            </button>
          </div>
        )}
      </div>
    </div>
    </div>
  )
}

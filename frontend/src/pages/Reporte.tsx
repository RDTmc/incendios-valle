import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trees, Home, MapPin, Camera, ShieldCheck, Flame } from 'lucide-react'
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet'
import L from 'leaflet'
import { useAuth } from '../App'
import { API } from '../api'
import { useToast } from '../util/toast'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
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

function createUserMarkerIcon() {
  return L.divIcon({
    className: '',
    html: `<div style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;background:#2563eb;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.3);"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="white" width="14" height="14"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
  })
}

function MapController({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap()
  useEffect(() => {
    map.setView([lat, lng], 15, { animate: true })
    setTimeout(() => map.invalidateSize(), 200)
  }, [map, lat, lng])
  return null
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
  const [gpsError, setGpsError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const { addToast } = useToast()
  const [misReportesCount] = useState(() => {
    try {
      const stored = localStorage.getItem('mis_reportes_ids')
      return stored ? JSON.parse(stored).length : 0
    } catch { return 0 }
  })
  const slotsLlenos = misReportesCount >= 5

  const getLocation = () => {
    if (!navigator.geolocation) {
      setGpsError('Tu dispositivo no soporta geolocalización')
      return
    }
    setLoading(true)
    setGpsError(null)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setReporte({
          ...reporte,
          lat: position.coords.latitude,
          lng: position.coords.longitude
        })
        setLoading(false)
        setGpsError(null)
      },
      (error) => {
        setLoading(false)
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setGpsError('Permiso de ubicación denegado. Actívalo en los ajustes del dispositivo.')
            break
          case error.POSITION_UNAVAILABLE:
            setGpsError('GPS no disponible. Verifica que esté activado.')
            break
          case error.TIMEOUT:
            setGpsError('La obtención de ubicación tardó demasiado. Intenta en un área abierta.')
            break
          default:
            setGpsError('Error al obtener ubicación. Intenta de nuevo.')
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!reporte.lat || !reporte.lng) {
      addToast('Obtén tu ubicación primero', 'warning')
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

      try {
        const ids = JSON.parse(localStorage.getItem('mis_reportes_ids') || '[]')
        ids.push(result.report_id)
        localStorage.setItem('mis_reportes_ids', JSON.stringify(ids))
      } catch {}

      navigate('/confirmar', { state: { reporte: result, lat: reporte.lat, lng: reporte.lng, tipo: reporte.tipo, fotoUrl: reporte.fotoUrl, isAnonymous } })
    } catch (err: any) {
      console.error('Error al enviar:', err)
      addToast(err.message || 'Error al enviar reporte. Intenta de nuevo.', 'error')
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
      addToast(err.message || 'Error al subir imagen. Intenta de nuevo.', 'error')
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
              <Button variant="ghost" size="sm" className="!text-red-600 hover:!text-red-800" onClick={() => { logout(); navigate('/login') }}>
                Cerrar
              </Button>
            </div>
          )}

          <Card>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Tipo de incendio */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Tipo de Incendio
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  type="button"
                  variant={reporte.tipo === 'FORESTAL' ? 'primary' : 'secondary'}
                  size="md"
                  icon={<Trees className="w-4 h-4" />}
                  onClick={() => setReporte({ ...reporte, tipo: 'FORESTAL' })}
                >
                  Forestal
                </Button>
                <Button
                  type="button"
                  variant={reporte.tipo === 'URBANO' ? 'primary' : 'secondary'}
                  size="md"
                  icon={<Home className="w-4 h-4" />}
                  onClick={() => setReporte({ ...reporte, tipo: 'URBANO' })}
                >
                  Urbano
                </Button>
              </div>
            </div>

            {/* Ubicación */}
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Ubicación
              </label>
              <Button
                type="button"
                variant="primary"
                size="md"
                icon={<MapPin className="w-4 h-4" />}
                loading={loading}
                disabled={loading}
                onClick={getLocation}
                className="w-full !bg-blue-500 hover:!bg-blue-600"
              >
                {loading ? 'Obteniendo ubicación...' : 'Obtener Mi Ubicación'}
              </Button>
              {gpsError && (
                <p className="mt-1 text-xs text-red-600 flex items-start gap-1">
                  <span>⚠️</span> {gpsError}
                </p>
              )}
              {reporte.lat && reporte.lng && (
                <p className="mt-1 text-xs text-green-600">
                  ✅ Ubicación: {reporte.lat.toFixed(4)}, {reporte.lng.toFixed(4)}
                </p>
              )}

              {/* Mapa compacto de previsualización */}
              {reporte.lat && reporte.lng && (
                <div className="mt-2 rounded-lg overflow-hidden border border-gray-200 h-40">
                  <MapContainer
                    center={[reporte.lat, reporte.lng]}
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
                    <MapController lat={reporte.lat} lng={reporte.lng} />
                    <Marker position={[reporte.lat, reporte.lng]} icon={createUserMarkerIcon()} />
                  </MapContainer>
                </div>
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

            {/* Indicador slots disponibles */}
            <div className="flex justify-between items-center text-xs text-gray-500">
              <span>Reportes activos: {misReportesCount}/5</span>
              {slotsLlenos && (
                <span className="text-red-600 font-medium">Límite alcanzado</span>
              )}
            </div>

            {/* Botón enviar */}
            {slotsLlenos ? (
              <div className="w-full bg-gray-300 text-gray-600 font-semibold py-3 rounded-lg text-sm text-center">
                Has alcanzado el límite máximo de 5 reportes simultáneos para evitar saturación del servicio.
              </div>
            ) : (
              <Button
                type="submit"
                loading={submitting}
                size="lg"
                className="w-full"
              >
                {submitting ? 'Enviando...' : 'Enviar Reporte'}
              </Button>
            )}
          </form>
        </Card>

        {isAnonymous && (
          <div className="mt-2 text-center">
            <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
              ¿Ya tienes cuenta? Inicia sesión aquí
            </Button>
          </div>
        )}
      </div>
    </div>
    </div>
  )
}

// Simulación de datos de focos
const focosMock = [
  { id: '1', lat: -33.45, lng: -70.66, estado: 'ACTIVO', prioridad: 'ALTA' },
  { id: '2', lat: -33.48, lng: -70.70, estado: 'CONTROLADO', prioridad: 'BAJA' },
  { id: '3', lat: -33.44, lng: -70.65, estado: 'ACTIVO', prioridad: 'MEDIA' },
]

export default function MapaFocos() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-fire-500 text-white p-4">
        <h1 className="text-lg font-bold">Mapa de Focos Activos</h1>
        <p className="text-sm opacity-90">3 focos en tiempo real</p>
      </div>

      {/* Mapa simulado */}
      <div className="h-[calc(100vh-140px)] bg-gray-200 relative">
        {/*模拟地图背景*/}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <span className="text-6xl">🗺️</span>
            <p className="text-gray-600 mt-4">Mapa de Google (integración)</p>
            <p className="text-xs text-gray-500">3 focos activos</p>
          </div>
        </div>

        {/* Leyenda */}
        <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-3">
          <h3 className="text-sm font-semibold mb-2">Leyenda:</h3>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-red-500 rounded-full"></span>
              <span className="text-xs">Alta prioridad</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-orange-500 rounded-full"></span>
              <span className="text-xs">Media prioridad</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 bg-yellow-500 rounded-full"></span>
              <span className="text-xs">Baja prioridad</span>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de focos */}
      <div className="bg-white p-4 border-t">
        <h3 className="font-semibold mb-3">Focos Recientes:</h3>
        <div className="space-y-2">
          {focosMock.map((foco) => (
            <div key={foco.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <div>
                <p className="font-medium text-sm">Foco #{foco.id}</p>
                <p className="text-xs text-gray-500">{foco.lat.toFixed(2)}, {foco.lng.toFixed(2)}</p>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${
                foco.prioridad === 'ALTA' ? 'bg-red-100 text-red-700' :
                foco.prioridad === 'MEDIA' ? 'bg-orange-100 text-orange-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>
                {foco.estado}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
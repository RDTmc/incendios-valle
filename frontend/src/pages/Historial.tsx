// Simulación de reportes del usuario
const reportesMock = [
  { id: 'RPT-001', tipo: 'FORESTAL', estado: 'VALIDADO', fecha: '2024-01-15 14:30' },
  { id: 'RPT-002', tipo: 'URBANO', estado: 'CONTROLADO', fecha: '2024-01-14 10:15' },
  { id: 'RPT-003', tipo: 'FORESTAL', estado: 'PENDIENTE', fecha: '2024-01-13 16:45' },
]

export default function Historial() {
  const getEstadoColor = (estado: string) => {
    switch (estado) {
      case 'VALIDADO': return 'bg-green-100 text-green-700'
      case 'CONTROLADO': return 'bg-blue-100 text-blue-700'
      case 'PENDIENTE': return 'bg-yellow-100 text-yellow-700'
      case 'RECHAZADO': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white p-4 shadow">
        <h1 className="text-xl font-bold text-gray-800">Mis Reportes</h1>
      </div>

      {/* Lista de reportes */}
      <div className="p-4 space-y-4">
        {reportesMock.map((reporte) => (
          <div key={reporte.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-semibold text-gray-800">{reporte.id}</h3>
                <p className="text-sm text-gray-500">{reporte.fecha}</p>
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
            </div>

            <button className="mt-3 text-sm text-fire-500 hover:underline">
              Ver detalles →
            </button>
          </div>
        ))}

        {reportesMock.length === 0 && (
          <div className="text-center py-8">
            <span className="text-4xl">📋</span>
            <p className="text-gray-500 mt-2">No tienes reportes aún</p>
          </div>
        )}
      </div>

      {/* Footer navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4">
        <div className="flex justify-around">
          <button className="text-gray-500">📋 Historial</button>
          <button className="text-fire-500 font-medium">🗺️ Mapa</button>
          <button className="text-gray-500">➕ Reportar</button>
        </div>
      </div>
    </div>
  )
}
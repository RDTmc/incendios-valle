import { Scan, Copy, Globe } from 'lucide-react'

export default function AfichePreview() {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full bg-white shadow-2xl rounded-xl overflow-hidden border">

        {/* Encabezado */}
        <div className="bg-fire-500 p-6 text-center text-white">
          <div className="w-full flex justify-center mb-6">
            <img
              src="/logo-muni.png"
              alt="Municipalidad de Valle del Sol"
              className="h-56 md:h-64 w-auto object-contain brightness-0 invert"
            />
          </div>
          <h1 className="text-xl font-bold">Incendios Valle del Sol</h1>
          <p className="text-sm opacity-90">Reporte Ciudadano de Emergencia</p>
        </div>

        {/* Cuerpo */}
        <div className="p-6 text-center">
          <p className="text-gray-700 font-medium mb-4">
            Escanea y reporta en 30 segundos
          </p>

          {/* QR */}
          <div className="bg-white p-4 inline-block rounded-lg shadow-md border border-gray-200 mb-4">
            <img
              src="/qr-pwa-incendios.png"
              alt="Codigo QR Incendios Valle del Sol"
              className="w-48 h-48 mx-auto"
            />
          </div>

          {/* Texto de contingencia Xiaomi */}
          <div className="bg-yellow-50 border-2 border-dashed border-yellow-500 rounded-lg p-4 text-left text-sm">
            <p className="font-semibold text-yellow-800 flex items-center gap-1 mb-2">
              <Scan className="w-4 h-4" /> Si tu telefono lee el codigo como texto:
            </p>
            <ol className="list-decimal list-inside text-yellow-900 space-y-1">
              <li>
                Presiona <strong className="text-yellow-950">Copiar</strong> <Copy className="w-3.5 h-3.5 inline-block" />
              </li>
              <li>
                Abre <strong>Google Chrome</strong> o <strong>Safari</strong> <Globe className="w-3.5 h-3.5 inline-block" />
              </li>
              <li>Pega la URL en la barra de direcciones</li>
              <li>Presiona Enter</li>
            </ol>
            <p className="mt-2 text-yellow-700 text-xs">
              O escribe manualmente: <strong className="text-yellow-900">incendios-valle.pages.dev</strong>
            </p>
          </div>

          {/* Pie */}
          <p className="text-xs text-gray-400 mt-4">
            App gratuita. No requiere registro para emergencias.
          </p>
        </div>
      </div>
    </div>
  )
}

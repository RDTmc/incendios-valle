import { Scan, Copy, Globe } from 'lucide-react'

export default function AfichePreview() {
  return (
    <div className="h-screen overflow-hidden bg-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white shadow-2xl rounded-xl overflow-hidden border max-h-full">

        {/* Encabezado */}
        <div className="bg-fire-500 p-4 text-center text-white">
          <div className="w-full flex justify-center mb-2">
            <img
              src="/logo-muni.png"
              alt="Municipalidad de Valle del Sol"
              className="h-56 md:h-64 w-auto object-contain brightness-0 invert"
            />
          </div>
          <h1 className="text-lg font-bold">Incendios Valle del Sol</h1>
          <p className="text-xs opacity-90">Reporte Ciudadano de Emergencia</p>
        </div>

        {/* Cuerpo */}
        <div className="p-4 text-center overflow-y-auto">
          <p className="text-gray-700 font-medium mb-2 text-sm">
            Escanea y reporta en 30 segundos
          </p>

          {/* QR */}
          <div className="bg-white p-2 inline-block rounded-lg shadow-md border border-gray-200 mb-2">
            <img
              src="/qr-pwa-incendios.png"
              alt="Codigo QR Incendios Valle del Sol"
              className="w-40 h-40 mx-auto"
            />
          </div>

          {/* Texto de contingencia Xiaomi */}
          <div className="bg-yellow-50 border-2 border-dashed border-yellow-500 rounded-lg p-3 text-left text-xs">
            <p className="font-semibold text-yellow-800 flex items-center gap-1 mb-1">
              <Scan className="w-3.5 h-3.5" /> Si tu telefono lee el codigo como texto:
            </p>
            <ol className="list-decimal list-inside text-yellow-900 space-y-0.5">
              <li>
                Presiona <strong className="text-yellow-950">Copiar</strong> <Copy className="w-3 h-3 inline-block" />
              </li>
              <li>
                Abre <strong>Google Chrome</strong> o <strong>Safari</strong> <Globe className="w-3 h-3 inline-block" />
              </li>
              <li>Pega la URL en la barra de direcciones</li>
              <li>Presiona Enter</li>
            </ol>
            <p className="mt-1 text-yellow-700 text-[10px]">
              O escribe: <strong className="text-yellow-900">incendios-valle.pages.dev</strong>
            </p>
          </div>

          {/* Pie */}
          <p className="text-[10px] text-gray-400 mt-2">
            App gratuita. No requiere registro para emergencias.
          </p>
        </div>
      </div>
    </div>
  )
}

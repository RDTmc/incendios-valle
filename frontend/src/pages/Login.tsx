import { useState } from 'react'
import { useAuth } from '../App'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/reporte')
    } catch (error) {
      alert('Error de autenticación')
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-fire-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🔥</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Incendios Valle del Sol</h1>
          <p className="text-gray-500">Sistema de Gestión de Emergencias</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent"
              placeholder="correo@ejemplo.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full bg-fire-500 hover:bg-fire-600 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Iniciar Sesión
          </button>
        </form>

        <div className="mt-6 text-center">
          <a href="#" className="text-sm text-fire-500 hover:underline">
            ¿Olvidaste tu contraseña?
          </a>
        </div>

        {/* Navegación temporal */}
        <div className="mt-8 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500 text-center mb-2">Navegación (demo):</p>
          <div className="flex flex-wrap gap-2 justify-center">
            <button onClick={() => navigate('/reporte')} className="text-xs bg-gray-100 px-2 py-1 rounded">Reporte</button>
            <button onClick={() => navigate('/mapa')} className="text-xs bg-gray-100 px-2 py-1 rounded">Mapa</button>
            <button onClick={() => navigate('/historial')} className="text-xs bg-gray-100 px-2 py-1 rounded">Historial</button>
          </div>
        </div>
      </div>
    </div>
  )
}
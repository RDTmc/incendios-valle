import { useState } from 'react'
import { useAuth } from '../App'
import { useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      // Navegación automática según rol (manejada por App.tsx)
    } catch (error: any) {
      alert(error.message || 'Error de autenticación')
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
              placeholder="correo@ejemplo.com"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3c-4.478 0-8.268 2.943-9.542 7-1.473 1.473-1.473 3.963-1.414 5.414l14 14a1 1 0 001.414-1.414l-1.473-1.473a10.014 10.014 0 00-3.542-7z" clipRule="evenodd" />
                    <path d="M14.5 10a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zM10 5.5a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            </div>
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

        {/* Navegación demo ELIMINADA - Rutas protegidas por rol */}
      </div>
    </div>
  )
}

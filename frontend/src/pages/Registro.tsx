import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { API } from '../api'
import { useToast } from '../util/toast'

export default function Registro() {
  const [nombre, setNombre] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { addToast } = useToast()

  const validateForm = (): boolean => {
    if (!nombre.trim()) {
      setError('Ingresa tu nombre')
      return false
    }
    if (!email.trim()) {
      setError('Ingresa tu correo electrónico')
      return false
    }
    if (!password) {
      setError('Ingresa una contraseña')
      return false
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return false
    }
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!validateForm()) return

    setLoading(true)
    try {
      await API.register(email, password, nombre)
      addToast('Registro exitoso. Ahora puedes iniciar sesión', 'success')
      navigate('/login')
    } catch (error: any) {
      const msg = error.message || 'Error al registrarse'
      setError(msg)
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <div className="text-center mb-6">
          <img
            src="/logo-muni.png"
            alt="Municipalidad de Valle del Sol"
            className="h-32 mx-auto mb-3 object-contain"
          />
          <h1 className="text-xl font-bold text-gray-800">Crear Cuenta</h1>
          <p className="text-sm text-gray-500">Regístrate para reportar incendios</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre completo
            </label>
            <input
              type="text"
              value={nombre}
              onChange={(e) => { setNombre(e.target.value); setError('') }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
              placeholder="Tu nombre"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correo electrónico
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError('') }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
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
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
              placeholder="Mínimo 6 caracteres"
              required
              minLength={6}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirmar contraseña
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => { setConfirmPassword(e.target.value); setError('') }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400"
              placeholder="Repite la contraseña"
              required
            />
          </div>

          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-fire-500 hover:bg-fire-600 text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Registrando...' : 'Crear Cuenta'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <Link to="/login" className="text-sm text-fire-500 hover:text-fire-600 underline">
            ¿Ya tienes cuenta? Inicia sesión
          </Link>
        </div>
      </div>
    </div>
  )
}

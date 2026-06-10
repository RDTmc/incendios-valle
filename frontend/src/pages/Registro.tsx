import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { API } from '../api'
import { useToast } from '../util/toast'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'

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
      <Card padding="lg" className="bg-white w-full max-w-md">
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
          <Input
            label="Nombre completo"
            type="text"
            value={nombre}
            onChange={(e) => { setNombre(e.target.value); setError('') }}
            placeholder="Tu nombre"
            required
          />

          <Input
            label="Correo electrónico"
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError('') }}
            placeholder="correo@ejemplo.com"
            required
          />

          <Input
            label="Contraseña"
            type="password"
            value={password}
            onChange={(e) => { setPassword(e.target.value); setError('') }}
            placeholder="Mínimo 6 caracteres"
            required
            minLength={6}
          />

          <Input
            label="Confirmar contraseña"
            type="password"
            value={confirmPassword}
            onChange={(e) => { setConfirmPassword(e.target.value); setError('') }}
            placeholder="Repite la contraseña"
            required
          />

          {error && (
            <p className="text-red-500 text-sm">{error}</p>
          )}

          <Button
            type="submit"
            loading={loading}
            size="lg"
            className="w-full"
          >
            {loading ? 'Registrando...' : 'Crear Cuenta'}
          </Button>
        </form>

        <div className="mt-4 text-center">
          <Link to="/login" className="text-sm text-fire-500 hover:text-fire-600 underline">
            ¿Ya tienes cuenta? Inicia sesión
          </Link>
        </div>
      </Card>
    </div>
  )
}

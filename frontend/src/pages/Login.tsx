import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Flame, ShieldCheck, ArrowLeft } from 'lucide-react'
import { useAuth } from '../App'
import { useToast } from '../util/toast'
import { API } from '../api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [twoFactorStep, setTwoFactorStep] = useState(false)
  const [tempToken, setTempToken] = useState('')
  const [otpCode, setOtpCode] = useState(['', '', '', '', '', ''])
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])
  const { login, setAuthFrom2FA } = useAuth()
  const navigate = useNavigate()
  const { addToast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!email.trim()) {
      setError('Ingresa tu correo electrónico')
      return
    }
    if (!password) {
      setError('Ingresa tu contraseña')
      return
    }

    setLoading(true)
    try {
      const res = await API.login(email, password)
      if (res.two_factor_required) {
        setTempToken(res.temp_token)
        setTwoFactorStep(true)
        addToast('Revisa tu correo para el código de verificación', 'info')
      } else {
        setAuthFrom2FA(res.token, res.user)
        addToast('Inicio de sesión exitoso', 'success')
      }
    } catch (error: any) {
      const msg = error.message || 'Error de autenticación'
      setError(msg)
      addToast(msg, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleOtpChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return
    const newOtp = [...otpCode]
    newOtp[index] = value
    setOtpCode(newOtp)
    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus()
    }
  }

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpCode[index] && index > 0) {
      otpRefs.current[index - 1]?.focus()
    }
  }

  const handleOtpSubmit = async () => {
    const code = otpCode.join('')
    if (code.length !== 6) {
      setError('Ingresa el código completo de 6 dígitos')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res = await API.login2FA(tempToken, code)
      setAuthFrom2FA(res.token, res.user)
      addToast('Inicio de sesión exitoso', 'success')
    } catch (error: any) {
      const msg = error.message || 'Código inválido'
      setError(msg)
      addToast(msg, 'error')
      setOtpCode(['', '', '', '', '', ''])
      otpRefs.current[0]?.focus()
    } finally {
      setLoading(false)
    }
  }

  const handleBackToLogin = () => {
    setTwoFactorStep(false)
    setOtpCode(['', '', '', '', '', ''])
    setError('')
  }

  if (twoFactorStep) {
    return (
      <div className="h-screen overflow-hidden bg-gray-100 flex items-center justify-center p-4">
        <Card padding="lg" className="bg-white w-full max-w-md">
          <div className="text-center mb-6">
            <ShieldCheck className="w-12 h-12 text-fire-500 mx-auto mb-2" />
            <h1 className="text-xl font-bold text-gray-800">Verificación en dos pasos</h1>
            <p className="text-sm text-gray-500 mt-1">
              Ingresa el código de 6 dígitos enviado a tu correo
            </p>
          </div>

          <div className="flex justify-center gap-2 mb-6">
            {otpCode.map((digit, i) => (
              <input
                key={i}
                ref={(el) => { otpRefs.current[i] = el }}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleOtpChange(i, e.target.value)}
                onKeyDown={(e) => handleOtpKeyDown(i, e)}
                className="w-12 h-14 text-center text-2xl font-bold border-2 border-gray-300 rounded-lg focus:border-fire-500 focus:ring-2 focus:ring-fire-500 outline-none bg-gray-900 text-white"
                autoFocus={i === 0}
              />
            ))}
          </div>

          {error && (
            <p className="text-red-500 text-sm text-center mb-4">{error}</p>
          )}

          <Button
            onClick={handleOtpSubmit}
            loading={loading}
            size="lg"
            className="w-full mb-3"
          >
            {loading ? 'Verificando...' : 'Verificar código'}
          </Button>

          <button
            onClick={handleBackToLogin}
            className="w-full text-sm text-gray-500 hover:text-gray-700 flex items-center justify-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver al inicio de sesión
          </button>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden bg-gray-100 flex items-center justify-center p-4">
      <Card padding="lg" className="bg-white w-full max-w-md">
        <div className="text-center mb-4">
          <div className="w-full flex justify-center mb-3">
            <img
              src="/logo-muni.png"
              alt="Municipalidad de Valle del Sol"
              className="h-56 md:h-64 w-auto object-contain"
            />
          </div>
          <h1 className="text-xl font-bold text-gray-800">Incendios Valle del Sol</h1>
          <p className="text-sm text-gray-500">Sistema de Gestión de Emergencias</p>
        </div>

        <Button
          variant="danger"
          size="lg"
          icon={<Flame className="w-5 h-5 animate-pulse" />}
          onClick={() => navigate('/reporte')}
          className="w-full mb-4"
        >
          <span className="flex flex-col items-start leading-tight">
            <span className="text-sm">Reportar Emergencia Rápida</span>
            <span className="text-[10px] font-normal opacity-80">Anónimo · Sin registro</span>
          </span>
        </Button>

        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white text-gray-500">O inicia sesión</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <Input
            label="Correo electrónico"
            type="email"
            value={email}
            onChange={(e) => { setEmail(e.target.value); setError('') }}
            placeholder="correo@ejemplo.com"
            required
            error={error && !email.trim() ? error : undefined}
          />

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Contraseña
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError('') }}
                className={`w-full px-4 py-2 pr-10 border ${error && !password ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-fire-500 focus:border-transparent bg-gray-900 text-white placeholder-gray-400`}
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3c-4.478 0-8.268 2.943-9.542 7-1.473 1.473-1.473 3.963-1.414 5.414l14 14a1 1 0 001.414-1.414l-1.473-1.473a10.014 10.014 0 00-3.542-7z" clipRule="evenodd" />
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

          {error && (
            <p className="text-red-500 text-sm mt-1">{error}</p>
          )}

          <Button
            type="submit"
            loading={loading}
            size="lg"
            className="w-full"
          >
            {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
          </Button>
        </form>

        <div className="mt-4 text-center space-y-2">
          <Link to="/registro" className="text-sm text-fire-500 hover:text-fire-600 underline">
            ¿No tienes cuenta? Regístrate aquí
          </Link>
          <p className="text-xs text-gray-400">
            Al reportar de forma anónima se registrará un identificador único de dispositivo.
          </p>
        </div>
      </Card>
    </div>
  )
}

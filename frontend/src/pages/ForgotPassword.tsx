import { useState, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ShieldCheck, Mail, KeyRound, ArrowLeft, CheckCircle2, AlertTriangle } from 'lucide-react'
import { useToast } from '../util/toast'
import { API } from '../api'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'

type Step = 'email' | 'reset' | 'success'

export default function ForgotPassword() {
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [otpCode, setOtpCode] = useState(['', '', '', '', '', ''])
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [backupCode, setBackupCode] = useState('')
  const [showBackup, setShowBackup] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const otpRefs = useRef<(HTMLInputElement | null)[]>([])
  const navigate = useNavigate()
  const { addToast } = useToast()

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email.trim()) {
      setError('Ingresa tu correo electrónico')
      return
    }
    setLoading(true)
    try {
      await API.forgotPassword(email)
      setStep('reset')
      addToast('Código de verificación enviado a tu correo', 'info')
    } catch (error: any) {
      const msg = error.message || 'Error al enviar código'
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

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    const code = otpCode.join('')
    if (code.length !== 6) {
      setError('Ingresa el código completo de 6 dígitos')
      return
    }
    if (!password) {
      setError('Ingresa tu nueva contraseña')
      return
    }
    if (password.length < 6) {
      setError('La contraseña debe tener al menos 6 caracteres')
      return
    }
    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }

    setLoading(true)
    try {
      await API.resetPassword(email, code, password, backupCode || undefined)
      setStep('success')
      addToast('Contraseña restablecida correctamente', 'success')
    } catch (error: any) {
      const msg = error.message || 'Error al restablecer contraseña'
      setError(msg)
      addToast(msg, 'error')
      if (msg.includes('Código') || msg.includes('backup')) {
        setOtpCode(['', '', '', '', '', ''])
        otpRefs.current[0]?.focus()
      }
    } finally {
      setLoading(false)
    }
  }

  if (step === 'success') {
    return (
      <div className="h-screen overflow-hidden bg-gray-100 flex items-center justify-center p-4">
        <Card padding="lg" className="bg-white w-full max-w-md text-center">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-gray-800 mb-2">Contraseña actualizada</h1>
          <p className="text-gray-500 mb-6">
            Tu contraseña se ha restablecido correctamente. Ya puedes iniciar sesión con tu nueva contraseña.
          </p>
          <Button onClick={() => navigate('/login')} size="lg" className="w-full">
            Ir a Iniciar Sesión
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden bg-gray-100 flex items-center justify-center p-4">
      <Card padding="lg" className="bg-white w-full max-w-md">
        <div className="text-center mb-6">
          {step === 'email' ? (
            <KeyRound className="w-12 h-12 text-fire-500 mx-auto mb-2" />
          ) : (
            <ShieldCheck className="w-12 h-12 text-fire-500 mx-auto mb-2" />
          )}
          <h1 className="text-xl font-bold text-gray-800">Recuperar Contraseña</h1>
          <p className="text-sm text-gray-500 mt-1">
            {step === 'email'
              ? 'Ingresa tu correo para recibir un código de verificación'
              : 'Ingresa el código de 6 dígitos recibido y tu nueva contraseña'
            }
          </p>
        </div>

        {step === 'email' ? (
          <form onSubmit={handleSendOTP} className="space-y-4">
            <Input
              label="Correo electrónico"
              type="email"
              value={email}
              onChange={(e) => { setEmail(e.target.value); setError('') }}
              placeholder="correo@ejemplo.com"
              required
              error={error ? error : undefined}
            />

            <Button type="submit" loading={loading} size="lg" className="w-full">
              {loading ? 'Enviando...' : 'Enviar Código de Verificación'}
            </Button>

            <Link to="/login" className="block text-center text-sm text-fire-500 hover:text-fire-600 underline">
              Volver a Iniciar Sesión
            </Link>
          </form>
        ) : (
          <form onSubmit={handleReset} className="space-y-4">
            <div className="text-center text-sm text-gray-500 mb-2">
              <Mail className="w-4 h-4 inline mr-1" />
              Código enviado a <span className="font-medium text-gray-700">{email}</span>
            </div>

            <div className="flex justify-center gap-2 mb-2">
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

            <Input
              label="Nueva contraseña"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError('') }}
              placeholder="Mínimo 6 caracteres"
              required
            />

            <Input
              label="Confirmar contraseña"
              type="password"
              value={confirmPassword}
              onChange={(e) => { setConfirmPassword(e.target.value); setError('') }}
              placeholder="Repite la contraseña"
              required
            />

            <div>
              <button
                type="button"
                onClick={() => setShowBackup(!showBackup)}
                className="text-xs text-gray-500 hover:text-gray-700 underline flex items-center gap-1"
              >
                <AlertTriangle className="w-3 h-3" />
                {showBackup ? 'Ocultar' : '¿Tienes un código de respaldo 2FA?'}
              </button>
              {showBackup && (
                <Input
                  label="Código de respaldo (opcional)"
                  type="text"
                  value={backupCode}
                  onChange={(e) => setBackupCode(e.target.value)}
                  placeholder="XXXXXX-XXXXXX"
                  className="mt-2"
                />
              )}
            </div>

            {error && (
              <p className="text-red-500 text-sm">{error}</p>
            )}

            <Button type="submit" loading={loading} size="lg" className="w-full">
              {loading ? 'Restableciendo...' : 'Restablecer Contraseña'}
            </Button>

            <button
              type="button"
              onClick={() => setStep('email')}
              className="w-full text-sm text-gray-500 hover:text-gray-700 flex items-center justify-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" />
              Volver al paso anterior
            </button>
          </form>
        )}
      </Card>
    </div>
  )
}

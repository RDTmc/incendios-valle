import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../App'
import { API } from '../api'
import { Button } from './ui/Button'
import { useToast } from '../util/toast'

export default function Admin2FATab() {
  const { token } = useAuth()
  const { addToast } = useToast()

  const [twoFAEnabled, setTwoFAEnabled] = useState(false)
  const [twoFARemaining, setTwoFARemaining] = useState(0)
  const [twoFALoading, setTwoFALoading] = useState(false)
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)

  const load2FAStatus = useCallback(async () => {
    if (!token) return
    setTwoFALoading(true)
    try {
      const res = await API.get2FAStatus(token)
      setTwoFAEnabled(res.enabled)
      setTwoFARemaining(res.remaining_backup_codes)
    } catch {
      // ignore
    } finally {
      setTwoFALoading(false)
    }
  }, [token])

  useEffect(() => { load2FAStatus() }, [load2FAStatus])

  const handleSetup2FA = async () => {
    if (!token) return
    setTwoFALoading(true)
    try {
      const res = await API.setup2FA(token)
      setTwoFAEnabled(true)
      setTwoFARemaining(res.backup_codes ? res.backup_codes.length : 0)
      setBackupCodes(res.backup_codes)
      addToast('2FA activado correctamente', 'success')
    } catch (error: any) {
      addToast(error.message || 'Error al activar 2FA', 'error')
    } finally {
      setTwoFALoading(false)
    }
  }

  const handleDisable2FA = async () => {
    if (!token) return
    if (!confirm('¿Estás seguro de desactivar la verificación en dos pasos?')) return
    setTwoFALoading(true)
    try {
      await API.disable2FA(token)
      setTwoFAEnabled(false)
      setTwoFARemaining(0)
      setBackupCodes(null)
      addToast('2FA desactivado', 'success')
    } catch (error: any) {
      addToast(error.message || 'Error al desactivar 2FA', 'error')
    } finally {
      setTwoFALoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Verificación en dos pasos</h3>
      <p className="text-gray-400 text-sm">
        Agrega una capa extra de seguridad a tu cuenta. Al activar esta opción,
        se te enviará un código de verificación a tu correo cada vez que inicies sesión.
      </p>

      {backupCodes && (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-lg p-4">
          <h4 className="text-yellow-400 font-semibold mb-2">Códigos de respaldo</h4>
          <p className="text-yellow-300 text-sm mb-3">
            Guarda estos códigos en un lugar seguro. Cada código solo puede usarse una vez.
            Si pierdes el acceso a tu correo, usa uno de estos códigos para iniciar sesión.
          </p>
          <div className="grid grid-cols-2 gap-2">
            {backupCodes.map((code, i) => (
              <code key={i} className="text-white bg-gray-900 px-3 py-2 rounded text-sm font-mono text-center">
                {code}
              </code>
            ))}
          </div>
          <button
            onClick={() => setBackupCodes(null)}
            className="mt-3 text-sm text-yellow-400 hover:text-yellow-300 underline"
          >
            Ya guardé los códigos
          </button>
        </div>
      )}

      {!backupCodes && (
        <div className="bg-gray-700 rounded-lg p-4">
          {twoFAEnabled ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-green-400 font-medium">Verificación en dos pasos activada</span>
              </div>
              <p className="text-gray-400 text-sm">
                Códigos de respaldo restantes: <strong className="text-white">{twoFARemaining}</strong>
              </p>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDisable2FA}
                loading={twoFALoading}
                className="!text-red-400 hover:!text-red-300"
              >
                Desactivar verificación en dos pasos
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-gray-400">La verificación en dos pasos está <strong className="text-white">desactivada</strong>.</p>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSetup2FA}
                loading={twoFALoading}
              >
                Activar verificación en dos pasos
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

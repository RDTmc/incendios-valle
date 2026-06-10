import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../App'
import { API } from '../api'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'

interface AdminUser {
  user_id: string
  email: string
  nombre: string
  rol: string
  created_at: string
}

interface AuditEntry {
  action: string
  admin_id: string
  target_id: string
  details: string
  created_at: string
}

type Tab = 'users' | 'audit'

type ModalMode = 'create' | 'edit' | null

const roles = ['VECINO', 'ADMIN']

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('es-CL')
  } catch {
    return dateStr
  }
}

export default function AdminPage() {
  const { user, token, logout } = useAuth()
  const navigate = useNavigate()

  const [tab, setTab] = useState<Tab>('users')

  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const [auditLog, setAuditLog] = useState<AuditEntry[]>([])
  const [loadingAudit, setLoadingAudit] = useState(false)

  const [modalMode, setModalMode] = useState<ModalMode>(null)
  const [editUser, setEditUser] = useState<AdminUser | null>(null)
  const [formEmail, setFormEmail] = useState('')
  const [formPassword, setFormPassword] = useState('')
  const [formNombre, setFormNombre] = useState('')
  const [formRol, setFormRol] = useState('VECINO')
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null)
  const [deleting, setDeleting] = useState(false)

  const fetchUsers = useCallback(async () => {
    if (!token) return
    setLoading(true)
    try {
      const data = await API.adminGetUsers(token, search || undefined)
      setUsers(data.users || [])
    } catch (err) {
      console.error('Error fetching users:', err)
    } finally {
      setLoading(false)
    }
  }, [token, search])

  const fetchAuditLog = useCallback(async () => {
    if (!token) return
    setLoadingAudit(true)
    try {
      const data = await API.getAuditLog(token, 200)
      setAuditLog(data || [])
    } catch (err) {
      console.error('Error fetching audit log:', err)
    } finally {
      setLoadingAudit(false)
    }
  }, [token])

  useEffect(() => { fetchUsers() }, [fetchUsers])
  useEffect(() => { if (tab === 'audit') fetchAuditLog() }, [tab, fetchAuditLog])

  function openCreateModal() {
    setModalMode('create')
    setEditUser(null)
    setFormEmail('')
    setFormPassword('')
    setFormNombre('')
    setFormRol('VECINO')
    setFormError('')
  }

  function openEditModal(u: AdminUser) {
    setModalMode('edit')
    setEditUser(u)
    setFormEmail(u.email)
    setFormPassword('')
    setFormNombre(u.nombre)
    setFormRol(u.rol)
    setFormError('')
  }

  function closeModal() {
    setModalMode(null)
    setEditUser(null)
  }

  async function handleSave() {
    if (!token) return
    setSaving(true)
    setFormError('')
    try {
      if (modalMode === 'create') {
        if (!formEmail || !formPassword) {
          setFormError('Email y contraseña son obligatorios')
          setSaving(false)
          return
        }
        await API.adminCreateUser(token, {
          email: formEmail,
          password: formPassword,
          nombre: formNombre,
          rol: formRol,
        })
      } else if (modalMode === 'edit' && editUser) {
        const data: { email?: string; nombre?: string; rol?: string } = {}
        if (formEmail !== editUser.email) data.email = formEmail
        if (formNombre !== editUser.nombre) data.nombre = formNombre
        if (formRol !== editUser.rol) data.rol = formRol
        await API.adminUpdateUser(token, editUser.user_id, data)
      }
      closeModal()
      fetchUsers()
      fetchAuditLog()
    } catch (err: any) {
      setFormError(err.message || 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    if (!token || !deleteTarget) return
    setDeleting(true)
    try {
      await API.adminDeleteUser(token, deleteTarget.user_id)
      setDeleteTarget(null)
      fetchUsers()
      fetchAuditLog()
    } catch (err: any) {
      console.error('Error deleting user:', err)
    } finally {
      setDeleting(false)
    }
  }

  function renderModal() {
    if (!modalMode) return null
    const isCreate = modalMode === 'create'
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md mx-4">
          <h2 className="text-lg font-bold text-white mb-4">
            {isCreate ? 'Crear Usuario' : 'Editar Usuario'}
          </h2>
          {formError && (
            <p className="text-red-400 text-sm mb-3">{formError}</p>
          )}
          <div className="space-y-3">
            <Input label="Email" type="email" value={formEmail} onChange={e => setFormEmail(e.target.value)} />
            {isCreate && (
              <Input label="Contraseña" type="password" value={formPassword} onChange={e => setFormPassword(e.target.value)} />
            )}
            <Input label="Nombre" value={formNombre} onChange={e => setFormNombre(e.target.value)} />
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Rol</label>
              <select
                value={formRol}
                onChange={e => setFormRol(e.target.value)}
                className="w-full px-4 py-2 border border-gray-600 rounded-lg bg-gray-900 text-white focus:ring-2 focus:ring-fire-500"
              >
                {roles.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-6">
            <Button variant="ghost" onClick={closeModal}>Cancelar</Button>
            <Button onClick={handleSave} loading={saving}>
              {isCreate ? 'Crear' : 'Guardar'}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  function renderDeleteConfirm() {
    if (!deleteTarget) return null
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-sm mx-4">
          <h2 className="text-lg font-bold text-white mb-2">Confirmar Eliminación</h2>
          <p className="text-gray-300 text-sm mb-4">
            ¿Eliminar al usuario <strong>{deleteTarget.email}</strong>? Esta acción no se puede deshacer.
          </p>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setDeleteTarget(null)}>Cancelar</Button>
            <Button variant="danger" onClick={handleDelete} loading={deleting}>Eliminar</Button>
          </div>
        </div>
      </div>
    )
  }

  function renderUsersTab() {
    return (
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Input
            placeholder="Buscar por email o nombre..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1"
          />
          <Button size="sm" onClick={() => fetchUsers()}>Buscar</Button>
          <Button size="sm" onClick={openCreateModal}>+ Nuevo</Button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-400">Cargando...</div>
        ) : users.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            {search ? 'Sin resultados' : 'No hay usuarios registrados'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="py-2 px-3">Email</th>
                  <th className="py-2 px-3">Nombre</th>
                  <th className="py-2 px-3">Rol</th>
                  <th className="py-2 px-3">Creado</th>
                  <th className="py-2 px-3">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.user_id} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-2 px-3 text-gray-200">{u.email}</td>
                    <td className="py-2 px-3 text-gray-300">{u.nombre || '—'}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.rol === 'ADMIN' ? 'bg-purple-900 text-purple-200' : 'bg-blue-900 text-blue-200'}`}>
                        {u.rol}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{formatDate(u.created_at)}</td>
                    <td className="py-2 px-3 flex gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEditModal(u)}>Editar</Button>
                      <Button variant="ghost" size="sm" className="!text-red-400 hover:!text-red-300" onClick={() => setDeleteTarget(u)}>Eliminar</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  function renderAuditTab() {
    return (
      <div>
        <p className="text-sm text-gray-400 mb-3">Registro de acciones administrativas</p>
        {loadingAudit ? (
          <div className="text-center py-8 text-gray-400">Cargando...</div>
        ) : auditLog.length === 0 ? (
          <div className="text-center py-8 text-gray-400">Sin registros aún</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="py-2 px-3">Acción</th>
                  <th className="py-2 px-3">Admin</th>
                  <th className="py-2 px-3">Target</th>
                  <th className="py-2 px-3">Detalle</th>
                  <th className="py-2 px-3">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {auditLog.map((entry, i) => (
                  <tr key={i} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        entry.action === 'create_user' ? 'bg-green-900 text-green-200' :
                        entry.action === 'update_user' ? 'bg-yellow-900 text-yellow-200' :
                        entry.action === 'delete_user' ? 'bg-red-900 text-red-200' :
                        'bg-gray-700 text-gray-200'
                      }`}>
                        {entry.action}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-300 font-mono text-xs">{entry.admin_id.slice(0, 8)}</td>
                    <td className="py-2 px-3 text-gray-300 font-mono text-xs">{entry.target_id?.slice(0, 8) || '—'}</td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{entry.details}</td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{formatDate(entry.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white pb-8">
      <div className="bg-gray-800 p-4 shadow flex items-center justify-between">
        <h1 className="text-xl font-bold">Admin Panel</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400 truncate max-w-[120px]">{user?.nombre || user?.email}</span>
          <Button variant="ghost" size="sm" className="!text-red-400 hover:!text-red-300" onClick={() => { logout(); navigate('/login') }}>
            Salir
          </Button>
        </div>
      </div>

      <div className="p-4">
        <div className="flex gap-2 mb-6">
          <Button
            variant={tab === 'users' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTab('users')}
          >
            Usuarios ({users.length})
          </Button>
          <Button
            variant={tab === 'audit' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTab('audit')}
          >
            Auditoría
          </Button>
        </div>

        <Card className="p-4">
          {tab === 'users' ? renderUsersTab() : renderAuditTab()}
        </Card>
      </div>

      {renderModal()}
      {renderDeleteConfirm()}
    </div>
  )
}

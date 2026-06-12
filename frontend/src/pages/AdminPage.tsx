import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../App'
import { API } from '../api'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { useToast } from '../util/toast'

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

interface ReportItem {
  report_id: string
  user_id: string
  tipo: string
  latitud: number
  longitud: number
  descripcion: string
  foto_url: string
  estado: string
  created_at: string
}

interface NotificationEntry {
  id: number
  type: string
  recipient_email: string
  recipient_name: string
  status: string
  sns_message_id: string
  created_at: string
}

type Tab = 'users' | 'audit' | 'notifications' | 'reports'

type ModalMode = 'create' | 'edit' | null

type SortKey = 'email' | 'nombre' | 'rol' | 'created_at'

const roles = ['VECINO', 'ADMIN']

const SORT_LABELS: Record<SortKey, string> = {
  email: 'Email',
  nombre: 'Nombre',
  rol: 'Rol',
  created_at: 'Creado',
}

function formatDate(dateStr: string) {
  try {
    return new Date(dateStr).toLocaleString('es-CL')
  } catch {
    return dateStr
  }
}

function sortUsers(users: AdminUser[], key: SortKey, asc: boolean): AdminUser[] {
  return [...users].sort((a, b) => {
    const aVal = a[key] || ''
    const bVal = b[key] || ''
    const cmp = aVal.localeCompare(bVal, 'es')
    return asc ? cmp : -cmp
  })
}

function Spinner() {
  return (
    <div className="flex justify-center py-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
    </div>
  )
}

export default function AdminPage() {
  const { token, logout } = useAuth()
  const navigate = useNavigate()
  const { addToast } = useToast()

  const [tab, setTab] = useState<Tab>('users')

  const [users, setUsers] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  const [auditLog, setAuditLog] = useState<AuditEntry[]>([])
  const [loadingAudit, setLoadingAudit] = useState(false)

  const [notifications, setNotifications] = useState<NotificationEntry[]>([])
  const [loadingNotifications, setLoadingNotifications] = useState(false)

  const [reports, setReports] = useState<ReportItem[]>([])
  const [loadingReports, setLoadingReports] = useState(false)
  const [reportFilter, setReportFilter] = useState('')
  const [updatingReport, setUpdatingReport] = useState<string | null>(null)

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

  const [sortKey, setSortKey] = useState<SortKey>('created_at')
  const [sortAsc, setSortAsc] = useState(false)

  const fetchUsers = useCallback(async (showLoader = true) => {
    if (!token) return
    if (showLoader) setLoading(true)
    try {
      const data = await API.adminGetUsers(token, search || undefined)
      setUsers(data.users || [])
    } catch {
      if (showLoader) addToast('Error al cargar usuarios', 'error')
    } finally {
      if (showLoader) setLoading(false)
    }
  }, [token, search])

  const fetchAuditLog = useCallback(async () => {
    if (!token) return
    setLoadingAudit(true)
    try {
      const data = await API.getAuditLog(token, 200)
      setAuditLog(data || [])
    } catch {
      addToast('Error al cargar registro de auditoría', 'error')
    } finally {
      setLoadingAudit(false)
    }
  }, [token])

  const fetchNotifications = useCallback(async () => {
    if (!token) return
    setLoadingNotifications(true)
    try {
      const data = await API.adminGetNotifications(token, 200)
      setNotifications(data || [])
    } catch {
      addToast('Error al cargar notificaciones', 'error')
    } finally {
      setLoadingNotifications(false)
    }
  }, [token])

  const fetchReports = useCallback(async () => {
    if (!token) return
    setLoadingReports(true)
    try {
      const data = await API.getReports(token)
      const items = Array.isArray(data) ? data : (Array.isArray(data?.reports) ? data.reports : [])
      setReports(items)
    } catch {
      addToast('Error al cargar reportes', 'error')
    } finally {
      setLoadingReports(false)
    }
  }, [token])

  useEffect(() => { fetchUsers() }, [fetchUsers])
  useEffect(() => { if (tab === 'audit') fetchAuditLog() }, [tab, fetchAuditLog])
  useEffect(() => { if (tab === 'notifications') fetchNotifications() }, [tab, fetchNotifications])
  useEffect(() => { if (tab === 'reports') fetchReports() }, [tab, fetchReports])

  useEffect(() => {
    const interval = setInterval(() => { fetchUsers(false) }, 15000)
    return () => clearInterval(interval)
  }, [fetchUsers])

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
  }

  const sortedUsers = sortUsers(users, sortKey, sortAsc)

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
    } catch {
      addToast('Error al eliminar usuario', 'error')
    } finally {
      setDeleting(false)
    }
  }

  async function handleUpdateReportStatus(reportId: string, estado: string) {
    if (!token) return
    setUpdatingReport(reportId)
    try {
      await API.updateReportStatus(token, reportId, estado)
      addToast(`Estado actualizado a ${estado}`, 'success')
      fetchReports()
    } catch (err: any) {
      addToast(err.message || 'Error al actualizar estado', 'error')
    } finally {
      setUpdatingReport(null)
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

  function renderSortIcon(key: SortKey) {
    if (sortKey !== key) return <span className="ml-1 text-gray-600">⇅</span>
    return <span className="ml-1">{sortAsc ? '↑' : '↓'}</span>
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
          <Spinner />
        ) : sortedUsers.length === 0 ? (
          <div className="text-center py-8 text-gray-300">
            {search ? 'Sin resultados' : 'No hay usuarios registrados'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  {(['email', 'nombre', 'rol', 'created_at'] as SortKey[]).map(key => (
                    <th
                      key={key}
                      className="py-2 px-3 cursor-pointer select-none hover:text-gray-200 transition-colors"
                      onClick={() => toggleSort(key)}
                    >
                      {SORT_LABELS[key]}
                      {renderSortIcon(key)}
                    </th>
                  ))}
                  <th className="py-2 px-3">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {sortedUsers.map(u => (
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
          <Spinner />
        ) : auditLog.length === 0 ? (
          <div className="text-center py-8 text-gray-300">Sin registros aún</div>
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

  function renderNotificationsTab() {
    return (
      <div>
        <p className="text-sm text-gray-400 mb-3">
          Notificaciones de bienvenida enviadas a nuevos usuarios
        </p>
        {loadingNotifications ? (
          <Spinner />
        ) : notifications.length === 0 ? (
          <div className="text-center py-8 text-gray-300">Sin notificaciones aún</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="py-2 px-3">Email</th>
                  <th className="py-2 px-3">Nombre</th>
                  <th className="py-2 px-3">Estado</th>
                  <th className="py-2 px-3">SNS ID</th>
                  <th className="py-2 px-3">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {notifications.map((n) => (
                  <tr key={n.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-2 px-3 text-gray-200">{n.recipient_email}</td>
                    <td className="py-2 px-3 text-gray-300">{n.recipient_name || '—'}</td>
                    <td className="py-2 px-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        n.status === 'sent' ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'
                      }`}>
                        {n.status === 'sent' ? 'Enviado' : 'Fallido'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-gray-400 font-mono text-xs">{n.sns_message_id || '—'}</td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{formatDate(n.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    )
  }

  const ESTADO_COLORS: Record<string, string> = {
    PENDIENTE: 'bg-yellow-900 text-yellow-200',
    ACTIVO: 'bg-red-900 text-red-200',
    CONTROLADO: 'bg-blue-900 text-blue-200',
    EXTINGUIDO: 'bg-gray-600 text-gray-200',
  }

  const filteredReports = reports.filter(r => {
    if (!reportFilter) return true
    const q = reportFilter.toLowerCase()
    return r.tipo.toLowerCase().includes(q) || (r.descripcion && r.descripcion.toLowerCase().includes(q)) || r.estado.toLowerCase().includes(q)
  })

  function renderReportsTab() {
    return (
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Input
            placeholder="Filtrar por tipo, descripción o estado..."
            value={reportFilter}
            onChange={e => setReportFilter(e.target.value)}
            className="flex-1"
          />
          <Button size="sm" onClick={() => fetchReports()}>Refrescar</Button>
        </div>

        {loadingReports ? (
          <Spinner />
        ) : filteredReports.length === 0 ? (
          <div className="text-center py-8 text-gray-300">
            {reportFilter ? 'Sin resultados' : 'No hay reportes'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400">
                  <th className="py-2 px-3">ID</th>
                  <th className="py-2 px-3">Tipo</th>
                  <th className="py-2 px-3">Descripción</th>
                  <th className="py-2 px-3">Ubicación</th>
                  <th className="py-2 px-3">Estado</th>
                  <th className="py-2 px-3">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map(r => (
                  <tr key={r.report_id} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-2 px-3 text-gray-400 font-mono text-xs">{r.report_id.slice(0, 8)}</td>
                    <td className="py-2 px-3 text-gray-200">{r.tipo}</td>
                    <td className="py-2 px-3 text-gray-300 max-w-xs truncate">{r.descripcion || '—'}</td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{r.latitud ? Number(r.latitud).toFixed(4) : '—'}, {r.longitud ? Number(r.longitud).toFixed(4) : '—'}</td>
                    <td className="py-2 px-3">
                      <select
                        value={r.estado}
                        onChange={e => handleUpdateReportStatus(r.report_id, e.target.value)}
                        disabled={updatingReport === r.report_id}
                        className={`px-2 py-1 rounded text-xs font-medium border-0 cursor-pointer ${
                          ESTADO_COLORS[r.estado] || 'bg-gray-700 text-gray-200'
                        } disabled:opacity-50`}
                      >
                        <option value="PENDIENTE">PENDIENTE</option>
                        <option value="ACTIVO">ACTIVO</option>
                        <option value="CONTROLADO">CONTROLADO</option>
                        <option value="EXTINGUIDO">EXTINGUIDO</option>
                      </select>
                    </td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{formatDate(r.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-gray-500 mt-2">Total: {filteredReports.length} reporte{filteredReports.length !== 1 ? 's' : ''}</p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white pb-8">
      <div className="bg-gray-800 p-4 shadow flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src="/logo-muni.png" alt="Municipalidad de Valle del Sol" className="h-14 w-auto" />
          <div>
            <h1 className="text-xl font-bold">Panel de Administración</h1>
            <p className="text-xs text-gray-400">Sistema de Gestión de Incendios</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold px-3 py-1.5 rounded bg-purple-900 text-purple-200 border border-purple-700">ADMIN</span>
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
          <Button
            variant={tab === 'notifications' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTab('notifications')}
          >
            Notificaciones ({notifications.length})
          </Button>
          <Button
            variant={tab === 'reports' ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => setTab('reports')}
          >
            Reportes ({reports.length})
          </Button>
        </div>

        <Card className="bg-gray-800 p-4">
          {tab === 'users' ? renderUsersTab() : tab === 'audit' ? renderAuditTab() : tab === 'notifications' ? renderNotificationsTab() : renderReportsTab()}
        </Card>
      </div>

      {renderModal()}
      {renderDeleteConfirm()}

      <div className="text-center text-xs text-gray-500 mt-8 px-4">
        Panel de Administración
        <br />
        Sistema de Gestión de Incendios
      </div>
    </div>
  )
}

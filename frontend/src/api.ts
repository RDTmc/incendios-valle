const API_URL = import.meta.env.VITE_API_URL || 'https://api.keogh.lat/api'

let onUnauthorized: (() => void) | null = null

export function setOnUnauthorized(fn: () => void) {
  onUnauthorized = fn
}

const handleAuth = async (res: Response): Promise<Response> => {
  if (res.status === 401 && onUnauthorized) {
    onUnauthorized()
  }
  return res
}

// P3-2: Safe JSON parser to handle non-JSON responses (403 HTML, plain text, etc.)
const safeJson = async (res: Response): Promise<any> => {
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return res.json()
  }
  const text = await res.text()
  try {
    return JSON.parse(text)
  } catch {
    return { error: text || `HTTP ${res.status}` }
  }
}

export const API = {
  login: async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Login failed: HTTP ${res.status}`)
    }
    return res.json()
  },

  register: async (email: string, password: string, nombre: string) => {
    const res = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, nombre, rol: 'VECINO' })
    })
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Register failed: HTTP ${res.status}`)
    }
    return res.json()
  },

  uploadImage: async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('file', file)
    const res = await handleAuth(await fetch(`${API_URL}/reports/upload`, {
      method: 'POST',
      body: formData
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Upload failed: HTTP ${res.status}`)
    }
    const result = await res.json()
    return result.foto_url
  },

  createReport: async (token: string, data: { user_id: string; tipo: string; latitud: number; longitud: number; descripcion: string; foto_url?: string }) => {
    const res = await handleAuth(await fetch(`${API_URL}/reports`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to create report: HTTP ${res.status}`)
    }
    return res.json()
  },

  getFocosActivos: async () => {
    const res = await fetch(`${API_URL}/focos-activos`)
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch focos: HTTP ${res.status}`)
    }
    return res.json()
  },

  getReports: async (token: string, userId?: string) => {
    const url = userId 
      ? `${API_URL}/reports?user_id=${userId}`
      : `${API_URL}/reports`
    const res = await handleAuth(await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch reports: HTTP ${res.status}`)
    }
    const text = await res.text()
    try {
      return JSON.parse(text)
    } catch {
      throw new Error('Failed to parse reports response')
    }
  },

  createReportAnonimo: async (data: { tipo: string; latitud: number; longitud: number; descripcion: string; foto_url?: string; device_id: string }) => {
    const res = await fetch(`${API_URL}/reportar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to create anonymous report: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminGetUsers: async (token: string, search?: string) => {
    const url = search ? `${API_URL}/admin/users?search=${encodeURIComponent(search)}` : `${API_URL}/admin/users`
    const res = await handleAuth(await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch users: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminCreateUser: async (token: string, data: { email: string; password: string; nombre: string; rol: string }) => {
    const res = await handleAuth(await fetch(`${API_URL}/admin/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(data)
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to create user: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminUpdateUser: async (token: string, userId: string, data: { email?: string; nombre?: string; rol?: string }) => {
    const res = await handleAuth(await fetch(`${API_URL}/admin/users/${userId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(data)
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to update user: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminDeleteUser: async (token: string, userId: string) => {
    const res = await handleAuth(await fetch(`${API_URL}/admin/users/${userId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to delete user: HTTP ${res.status}`)
    }
    return res.json()
  },

  getAuditLog: async (token: string, limit?: number) => {
    const url = limit ? `${API_URL}/admin/audit-log?limit=${limit}` : `${API_URL}/admin/audit-log`
    const res = await handleAuth(await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch audit log: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminGetNotifications: async (token: string, limit?: number) => {
    const url = limit ? `${API_URL}/admin/notifications?limit=${limit}` : `${API_URL}/admin/notifications`
    const res = await handleAuth(await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch notifications: HTTP ${res.status}`)
    }
    return res.json()
  },

  adminGetReports: async (token: string) => {
    const res = await handleAuth(await fetch(`${API_URL}/admin/reports`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch reports: HTTP ${res.status}`)
    }
    return res.json()
  },

  updateReportStatus: async (token: string, reportId: string, estado: string) => {
    const res = await handleAuth(await fetch(`${API_URL}/admin/reports/${reportId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({ estado })
    }))
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to update report status: HTTP ${res.status}`)
    }
    return res.json()
  }
}

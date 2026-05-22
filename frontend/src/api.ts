const API_URL = import.meta.env.VITE_API_URL || 'https://api.keogh.lat/api'

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

  createReport: async (token: string, data: { user_id: string; tipo: string; latitud: number; longitud: number; descripcion: string }) => {
    const res = await fetch(`${API_URL}/reports`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    })
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
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!res.ok) {
      const err = await safeJson(res)
      throw new Error(err.error || err.detail || `Failed to fetch reports: HTTP ${res.status}`)
    }
    return res.json()
  }
}

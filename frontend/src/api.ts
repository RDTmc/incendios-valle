const API_URL = 'http://3.227.186.158/api'

export const API = {
  login: async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || 'Login failed')
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
      const err = await res.json()
      throw new Error(err.error || 'Register failed')
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
      const err = await res.json()
      throw new Error(err.error || 'Failed to create report')
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
    if (!res.ok) throw new Error('Failed to fetch reports')
    return res.json()
  }
}
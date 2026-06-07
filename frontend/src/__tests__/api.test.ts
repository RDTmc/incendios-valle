import { describe, it, expect, vi, beforeEach } from 'vitest'

const API_URL = 'https://api.keogh.lat/api'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('API.login', () => {
  it('should login successfully with valid credentials', async () => {
    const mockResponse = {
      token: 'test-jwt-token',
      user: { user_id: '1', email: 'test@example.com', rol: 'VECINO', nombre: 'Test' }
    }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockResponse)
    })

    const { API } = await import('../api')
    const result = await API.login('test@example.com', 'password123')
    expect(result.token).toBe('test-jwt-token')
    expect(result.user.email).toBe('test@example.com')
  })

  it('should throw error on invalid credentials', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({ detail: 'Invalid credentials' })
    })

    const { API } = await import('../api')
    await expect(API.login('wrong@example.com', 'wrongpass')).rejects.toThrow('Invalid credentials')
  })

  it('should handle non-JSON error responses', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 403,
      headers: new Headers({ 'content-type': 'text/html' }),
      text: () => Promise.resolve('<html>Access Denied</html>')
    })

    const { API } = await import('../api')
    await expect(API.login('test@test.com', 'pass')).rejects.toThrow()
  })

  it('should handle network errors', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    const { API } = await import('../api')
    await expect(API.login('test@test.com', 'pass')).rejects.toThrow('Network error')
  })
})

describe('API.register', () => {
  it('should register a new user', async () => {
    const mockResponse = {
      token: 'new-jwt-token',
      user: { user_id: '2', email: 'new@example.com', rol: 'VECINO', nombre: 'New User' }
    }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockResponse)
    })

    const { API } = await import('../api')
    const result = await API.register('new@example.com', 'SecurePass1!', 'New User')
    expect(result.token).toBe('new-jwt-token')
    expect(result.user.nombre).toBe('New User')
  })

  it('should throw on duplicate email', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({ detail: 'User already exists' })
    })

    const { API } = await import('../api')
    await expect(API.register('existing@example.com', 'pass', 'Name')).rejects.toThrow('User already exists')
  })
})

describe('API.createReportAnonimo', () => {
  it('should create anonymous report with device_id', async () => {
    const mockResponse = { report_id: 'r1', estado: 'PENDIENTE', created_at: '2026-01-01T00:00:00' }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockResponse)
    })

    const { API } = await import('../api')
    const result = await API.createReportAnonimo({
      tipo: 'FORESTAL',
      latitud: -33.45,
      longitud: -70.67,
      descripcion: 'Test',
      device_id: 'device-001'
    })
    expect(result.report_id).toBe('r1')
    expect(result.estado).toBe('PENDIENTE')
  })

  it('should call the /reportar endpoint', async () => {
    let capturedUrl = ''
    let capturedBody = {}
    globalThis.fetch = vi.fn().mockImplementation((url: string, options: any) => {
      capturedUrl = url
      capturedBody = JSON.parse(options.body)
      return Promise.resolve({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ report_id: 'r1' })
      })
    })

    const { API } = await import('../api')
    await API.createReportAnonimo({
      tipo: 'URBANO',
      latitud: -33.45,
      longitud: -70.67,
      descripcion: 'Test',
      device_id: 'device-002'
    })
    expect(capturedUrl).toContain('/reportar')
    expect(capturedBody.tipo).toBe('URBANO')
    expect(capturedBody.device_id).toBe('device-002')
  })
})

describe('API.getFocosActivos', () => {
  it('should return active fire spots', async () => {
    const mockFocos = [
      { id: 'r1', lat: -33.45, lng: -70.67, estado: 'ACTIVO', tipo: 'FORESTAL' }
    ]
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockFocos)
    })

    const { API } = await import('../api')
    const result = await API.getFocosActivos()
    expect(result).toHaveLength(1)
    expect(result[0].estado).toBe('ACTIVO')
  })
})

describe('API.getReports', () => {
  it('should fetch reports with auth token', async () => {
    const mockReports = [{ report_id: 'r1', tipo: 'FORESTAL' }]
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockReports)
    })

    const { API } = await import('../api')
    const result = await API.getReports('test-token', 'user-1')
    expect(result).toHaveLength(1)
    expect(result[0].report_id).toBe('r1')
  })
})

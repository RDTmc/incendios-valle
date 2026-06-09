import { describe, it, expect, vi, beforeEach } from 'vitest'

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
    let capturedBody: Record<string, unknown> = {}
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

describe('API.createReport', () => {
  it('should create a report with auth token', async () => {
    const mockResponse = { report_id: 'r1', estado: 'PENDIENTE' }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockResponse)
    })

    const { API } = await import('../api')
    const result = await API.createReport('test-token', {
      user_id: 'u1',
      tipo: 'FORESTAL',
      latitud: -33.45,
      longitud: -70.67,
      descripcion: 'Test fire'
    })
    expect(result.report_id).toBe('r1')
    expect(result.estado).toBe('PENDIENTE')
  })

  it('should include Authorization header', async () => {
    let capturedHeaders: any = null
    globalThis.fetch = vi.fn().mockImplementation((url: string, options: any) => {
      capturedHeaders = options.headers
      return Promise.resolve({
        ok: true,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ report_id: 'r1' })
      })
    })

    const { API } = await import('../api')
    await API.createReport('my-token', {
      user_id: 'u1',
      tipo: 'URBANO',
      latitud: -33.45,
      longitud: -70.67,
      descripcion: 'Test'
    })
    expect(capturedHeaders['Authorization']).toBe('Bearer my-token')
  })
})

describe('API.uploadImage', () => {
  it('should upload an image and return url', async () => {
    const mockResponse = { foto_url: 'https://bucket.s3.amazonaws.com/test.jpg' }
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve(mockResponse)
    })

    const { API } = await import('../api')
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    const url = await API.uploadImage(file)
    expect(url).toBe('https://bucket.s3.amazonaws.com/test.jpg')
  })

  it('should throw on upload failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 413,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({ error: 'File too large' })
    })

    const { API } = await import('../api')
    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' })
    await expect(API.uploadImage(file)).rejects.toThrow('File too large')
  })
})

describe('API.setOnUnauthorized', () => {
  it('should call the registered callback on 401 responses', async () => {
    const callback = vi.fn()
    const { API, setOnUnauthorized } = await import('../api')
    setOnUnauthorized(callback)

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({ detail: 'Token expired' })
    })

    await expect(API.createReport('expired-token', {
      user_id: 'u1', tipo: 'FORESTAL', latitud: -33.45, longitud: -70.67, descripcion: 'Test'
    })).rejects.toThrow('Token expired')

    expect(callback).toHaveBeenCalled()
  })

  it('should not call callback on non-401 errors', async () => {
    const callback = vi.fn()
    const { API, setOnUnauthorized } = await import('../api')
    setOnUnauthorized(callback)

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      headers: new Headers({ 'content-type': 'application/json' }),
      json: () => Promise.resolve({ detail: 'Server error' })
    })

    await expect(API.createReport('token', {
      user_id: 'u1', tipo: 'FORESTAL', latitud: -33.45, longitud: -70.67, descripcion: 'Test'
    })).rejects.toThrow('Server error')

    expect(callback).not.toHaveBeenCalled()
  })
})

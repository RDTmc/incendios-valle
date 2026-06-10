import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { AuthContext, ProtectedRoute, useAuth, getDefaultPath } from '../App'

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
})

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => <div data-testid="map-container">{children}</div>,
  TileLayer: () => <div data-testid="tile-layer" />,
  Marker: ({ position }: any) => <div data-testid="marker" data-lat={position[0]} data-lng={position[1]} />,
  useMap: () => ({ setView: vi.fn(), invalidateSize: vi.fn() }),
}))

vi.mock('leaflet', () => ({
  default: { divIcon: () => ({}) },
  divIcon: () => ({}),
  Icon: { Default: { mergeOptions: vi.fn() } },
}))

vi.mock('../util/image', () => ({ compressImage: vi.fn() }))
vi.mock('../util/device', () => ({ getDeviceId: vi.fn().mockResolvedValue('test-device') }))

function createAuthValue(user: any, token: string | null) {
  return {
    user,
    token,
    login: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn(),
  }
}

function renderWithAuth(ui: React.ReactElement, user: any, token: string | null) {
  return render(
    <AuthContext.Provider value={createAuthValue(user, token)}>
      <MemoryRouter initialEntries={['/']}>
        {ui}
      </MemoryRouter>
    </AuthContext.Provider>
  )
}

describe('useAuth', () => {
  it('throws when used outside AuthProvider', () => {
    function Broken() { useAuth(); return null }
    expect(() => render(<Broken />)).toThrow('useAuth must be used within AuthProvider')
  })

  it('returns context value inside provider', () => {
    function Reader() {
      const auth = useAuth()
      return <div>{auth.user?.email}</div>
    }
    renderWithAuth(<Reader />, { email: 'test@test.cl', rol: 'VECINO' }, 'token123')
    expect(screen.getByText('test@test.cl')).toBeDefined()
  })
})

describe('ProtectedRoute', () => {
  it('redirects to /login when no user', () => {
    renderWithAuth(
      <ProtectedRoute><div>protected</div></ProtectedRoute>,
      null, null
    )
    expect(screen.queryByText('protected')).toBeNull()
  })

  it('renders children when allowAnonymous and no user', () => {
    renderWithAuth(
      <ProtectedRoute allowAnonymous><div>anonymous ok</div></ProtectedRoute>,
      null, null
    )
    expect(screen.getByText('anonymous ok')).toBeDefined()
  })

  it('renders children when user has allowed role', () => {
    renderWithAuth(
      <ProtectedRoute allowedRoles={['VECINO']}><div>authorized</div></ProtectedRoute>,
      { user_id: '1', email: 'v@v.cl', rol: 'VECINO', nombre: 'V' },
      'token'
    )
    expect(screen.getByText('authorized')).toBeDefined()
  })

  it('renders children when no role restriction', () => {
    renderWithAuth(
      <ProtectedRoute><div>any role</div></ProtectedRoute>,
      { user_id: '1', email: 'a@a.cl', rol: 'ADMIN', nombre: 'A' },
      'token'
    )
    expect(screen.getByText('any role')).toBeDefined()
  })

  it('redirects ADMIN to /admin when role not in allowedRoles', () => {
    renderWithAuth(
      <Routes>
        <Route path="/" element={<ProtectedRoute allowedRoles={['VECINO']}><div>vecino only</div></ProtectedRoute>} />
      </Routes>,
      { user_id: '1', email: 'a@a.cl', rol: 'ADMIN', nombre: 'A' },
      'token'
    )
    expect(screen.queryByText('vecino only')).toBeNull()
  })

  it('redirects VECINO to /vecino when role not in allowedRoles', () => {
    renderWithAuth(
      <Routes>
        <Route path="/" element={<ProtectedRoute allowedRoles={['ADMIN']}><div>admin only</div></ProtectedRoute>} />
      </Routes>,
      { user_id: '1', email: 'v@v.cl', rol: 'VECINO', nombre: 'V' },
      'token'
    )
    expect(screen.queryByText('admin only')).toBeNull()
  })
})

describe('getDefaultPath', () => {
  it('returns /login when user is null', () => {
    expect(getDefaultPath(null)).toBe('/login')
  })

  it('returns /admin for ADMIN role', () => {
    expect(getDefaultPath({ rol: 'ADMIN' })).toBe('/admin')
  })

  it('returns /reporte for non-admin role', () => {
    expect(getDefaultPath({ rol: 'VECINO' })).toBe('/reporte')
  })
})

describe('App routing', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it('renders Login page when no user in localStorage', async () => {
    localStorage.clear()
    const App = (await import('../App')).default
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Iniciar Sesión')).toBeDefined()
    })
  })

  it('renders Admin page when ADMIN user in localStorage', async () => {
    localStorage.setItem('incendios_user', JSON.stringify({ user_id: 'admin1', email: 'admin@test.cl', rol: 'ADMIN', nombre: 'Admin User' }))
    localStorage.setItem('incendios_token', 'admin-token')
    const App = (await import('../App')).default
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Panel de Administración')).toBeDefined()
    })
  })

  it('logout clears localStorage and shows Login page', async () => {
    localStorage.setItem('incendios_user', JSON.stringify({ user_id: 'admin1', email: 'admin@test.cl', rol: 'ADMIN', nombre: 'Admin User' }))
    localStorage.setItem('incendios_token', 'admin-token')
    const App = (await import('../App')).default
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Panel de Administración')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Salir'))
    await waitFor(() => {
      expect(localStorage.getItem('incendios_user')).toBeNull()
      expect(localStorage.getItem('incendios_token')).toBeNull()
      expect(screen.getByText('Iniciar Sesión')).toBeDefined()
    })
  })

  it('renders Reporte page when VECINO user in localStorage', async () => {
    localStorage.setItem('incendios_user', JSON.stringify({ user_id: 'vecino1', email: 'v@test.cl', rol: 'VECINO', nombre: 'Vecino' }))
    localStorage.setItem('incendios_token', 'vecino-token')
    const App = (await import('../App')).default
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Reportar Incendio')).toBeDefined()
    })
  })

  it('handles 401 API response by logging out', async () => {
    localStorage.setItem('incendios_user', JSON.stringify({ user_id: 'admin1', email: 'admin@test.cl', rol: 'ADMIN', nombre: 'Admin' }))
    localStorage.setItem('incendios_token', 'admin-token')

    const spy = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 401, statusText: 'Unauthorized', headers: { 'content-type': 'text/plain' } })
    )

    const App = (await import('../App')).default
    render(<App />)

    await waitFor(() => {
      expect(localStorage.getItem('incendios_user')).toBeNull()
      expect(screen.getByText('Iniciar Sesión')).toBeDefined()
    })

    spy.mockRestore()
  })

  it.skip('completes login flow and redirects to Reporte', async () => {
    localStorage.clear()

    const spy = vi.spyOn(globalThis, 'fetch').mockImplementation((url: string | URL | Request) => {
      if (url.toString().includes('/login')) {
        return Promise.resolve(new Response(JSON.stringify({
          token: 'new-token',
          user: { user_id: 'u1', email: 'new@test.cl', rol: 'VECINO', nombre: 'New User' }
        }), { status: 200, headers: { 'content-type': 'application/json' } }))
      }
      return Promise.resolve(new Response(null, { status: 404, headers: { 'content-type': 'text/plain' } }))
    })

    const App = (await import('../App')).default
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Iniciar Sesión')).toBeDefined()
    })

    const emailInput = screen.getByPlaceholderText(/correo@ejemplo/i)
    const passwordInput = screen.getByPlaceholderText('••••••••')
    const submitButton = screen.getByText('Iniciar Sesión')

    fireEvent.change(emailInput, { target: { value: 'new@test.cl' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Reportar Incendio')).toBeDefined()
    })

    expect(localStorage.getItem('incendios_token')).toBe('new-token')

    spy.mockRestore()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthContext, ProtectedRoute, useAuth, getDefaultPath } from '../App'

function createAuthValue(user: any, token: string | null) {
  return {
    user,
    token,
    login: vi.fn(),
    logout: vi.fn(),
  }
}

function renderWithAuth(ui: React.ReactElement, user: any, token: string | null) {
  return render(
    <AuthContext.Provider value={createAuthValue(user, token)}>
      <MemoryRouter>
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

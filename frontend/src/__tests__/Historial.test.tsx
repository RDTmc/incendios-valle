import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate, useLocation: () => ({ pathname: '/historial' }) }
})

const mockLogout = vi.fn()
let mockAuthValue = { user: { user_id: '1', email: 'test@test.cl', nombre: 'Test User', rol: 'VECINO' }, token: 'valid-token', logout: mockLogout, login: vi.fn() }
vi.mock('../App', () => ({ useAuth: () => mockAuthValue }))

const mockReports = [
  { report_id: 'rep-001', tipo: 'FORESTAL', estado: 'VALIDADO', created_at: '2026-01-15T10:00:00Z', latitud: '-33.45', longitud: '-70.67', descripcion: 'Incendio en laderas' },
  { report_id: 'rep-002', tipo: 'URBANO', estado: 'PENDIENTE', created_at: '2026-02-20T15:30:00Z', latitud: '-33.46', longitud: '-70.68', descripcion: '' },
]
const mockGetReports = vi.fn()
vi.mock('../api', () => ({ API: { getReports: (...args: any[]) => mockGetReports(...args) } }))

beforeEach(() => {
  vi.clearAllMocks()
  mockGetReports.mockResolvedValue(mockReports)
  mockAuthValue = { user: { user_id: '1', email: 'test@test.cl', nombre: 'Test User', rol: 'VECINO' }, token: 'valid-token', logout: mockLogout, login: vi.fn() }
})

describe('Historial Page', () => {
  it('shows loading state initially', async () => {
    mockGetReports.mockReturnValue(new Promise(() => {}))
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    expect(screen.getByText('Cargando...')).toBeDefined()
  })

  it('shows empty state when no reports', async () => {
    mockGetReports.mockResolvedValue([])
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('No tienes reportes aún')).toBeDefined()
    })
    expect(screen.getByText('Reportar un incendio')).toBeDefined()
  })

  it('renders report list', async () => {
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText(/Reporte #rep-001/)).toBeDefined()
      expect(screen.getByText(/Reporte #rep-002/)).toBeDefined()
    })
    expect(screen.getByText('VALIDADO')).toBeDefined()
    expect(screen.getByText('PENDIENTE')).toBeDefined()
    expect(screen.getByText('Incendio forestal')).toBeDefined()
    expect(screen.getByText('Incendio urbano')).toBeDefined()
    expect(screen.getByText('Incendio en laderas')).toBeDefined()
  })

  it('calls API.getReports with token and user_id', async () => {
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(mockGetReports).toHaveBeenCalledWith('valid-token', '1')
    })
  })

  it('shows user name and logout button', async () => {
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeDefined()
    })
    fireEvent.click(screen.getByText('Cerrar Sesión'))
    expect(mockLogout).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('renders BottomNav with active tab', async () => {
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getByText('Historial')).toBeDefined()
    })
    expect(screen.getByText('Mapa')).toBeDefined()
    expect(screen.getByText('Reportar')).toBeDefined()
  })

  it('navigates to /mapa when clicking Ver en mapa', async () => {
    const Historial = (await import('../pages/Historial')).default
    render(<MemoryRouter><ToastProvider><Historial /></ToastProvider></MemoryRouter>)
    await waitFor(() => {
      expect(screen.getAllByText('Ver en mapa →').length).toBeGreaterThanOrEqual(1)
    })
    fireEvent.click(screen.getAllByText('Ver en mapa →')[0])
    expect(mockNavigate).toHaveBeenCalledWith('/mapa', { state: { lat: -33.45, lng: -70.67, reportId: 'rep-001' } })
  })
})

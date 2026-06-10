import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockNavigate = vi.fn()
let mockLocationState: any = null
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate, useLocation: () => ({ state: mockLocationState }) }
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
}))

beforeEach(() => {
  vi.clearAllMocks()
  mockLocationState = null
})

describe('Confirmacion Page', () => {
  it('renders with location state', async () => {
    mockLocationState = {
      reporte: { report_id: 'abc-123', estado: 'PENDIENTE', created_at: '2026-03-10T12:00:00Z' },
      lat: -33.4489,
      lng: -70.6693,
      tipo: 'URBANO',
    }
    const Confirmacion = (await import('../pages/Confirmacion')).default
    render(<MemoryRouter><ToastProvider><Confirmacion /></ToastProvider></MemoryRouter>)
    expect(screen.getByText('Reporte Enviado')).toBeDefined()
    expect(screen.getByText('ID: abc-123')).toBeDefined()
    expect(screen.getByText(/Urbano/)).toBeDefined()
    expect(screen.getByText(/PENDIENTE/)).toBeDefined()
    expect(screen.getByTestId('map-container')).toBeDefined()
  })

  it('redirects to /reporte without location state', async () => {
    const Confirmacion = (await import('../pages/Confirmacion')).default
    render(<MemoryRouter><ToastProvider><Confirmacion /></ToastProvider></MemoryRouter>)
    expect(mockNavigate).toHaveBeenCalledWith('/reporte', { replace: true })
  })

  it('renders foto when present', async () => {
    mockLocationState = {
      reporte: { report_id: 'r1', estado: 'PENDIENTE', created_at: '' },
      lat: 0, lng: 0, tipo: 'FORESTAL',
      fotoUrl: 'https://cdn.example.com/foto.jpg',
    }
    const Confirmacion = (await import('../pages/Confirmacion')).default
    render(<MemoryRouter><ToastProvider><Confirmacion /></ToastProvider></MemoryRouter>)
    const img = screen.getByAltText('Foto del incendio') as HTMLImageElement
    expect(img).toBeDefined()
    expect(img.src).toContain('foto.jpg')
  })

  it('navigates to /reporte on Nuevo Reporte click', async () => {
    mockLocationState = {
      reporte: { report_id: 'r1', estado: 'PENDIENTE', created_at: '' },
      lat: 0, lng: 0, tipo: 'FORESTAL',
    }
    const Confirmacion = (await import('../pages/Confirmacion')).default
    render(<MemoryRouter><ToastProvider><Confirmacion /></ToastProvider></MemoryRouter>)
    fireEvent.click(screen.getByText('Nuevo Reporte'))
    expect(mockNavigate).toHaveBeenCalledWith('/reporte')
  })

  it('navigates to /mapa with state on Ver Mapa click', async () => {
    mockLocationState = {
      reporte: { report_id: 'r1', estado: 'PENDIENTE', created_at: '' },
      lat: -33.45, lng: -70.67, tipo: 'FORESTAL',
    }
    const Confirmacion = (await import('../pages/Confirmacion')).default
    render(<MemoryRouter><ToastProvider><Confirmacion /></ToastProvider></MemoryRouter>)
    fireEvent.click(screen.getByText('Ver Mapa de Focos'))
    expect(mockNavigate).toHaveBeenCalledWith('/mapa', {
      state: { centerTo: [-33.45, -70.67], highlightId: 'r1' },
    })
  })
})

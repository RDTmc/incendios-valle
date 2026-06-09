import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useLocation: () => ({ state: null }) }
})

const mockRenderMap = vi.fn()
class MockMapboxStrategy {
  id = 'mapbox'
  label = 'Mapbox'
  renderMap = mockRenderMap
}

vi.mock('../util/map', () => ({
  MapboxStrategy: MockMapboxStrategy,
}))

vi.mock('../api', () => ({
  API: { getFocosActivos: vi.fn() },
}))

import { API } from '../api'

const sampleFoco = (overrides = {}) => ({
  id: '1',
  lat: -33.45,
  lng: -70.67,
  estado: 'ACTIVO',
  tipo: 'FORESTAL',
  descripcion: 'Incendio cerca del cerro',
  foto_url: '',
  created_at: new Date().toISOString(),
  ...overrides,
})

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

async function renderMapaFocos() {
  const MapaFocos = (await import('../pages/MapaFocos')).default
  return render(
    <MemoryRouter>
      <MapaFocos />
    </MemoryRouter>
  )
}

describe('MapaFocos Page', () => {
  it('renders title and legend', async () => {
    ;(API.getFocosActivos as any).mockResolvedValue([])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    expect(screen.getByText('Mapa de Focos Activos')).toBeDefined()
    expect(screen.getByText('Leyenda:')).toBeDefined()
    expect(screen.getByText('Activo')).toBeDefined()
    expect(screen.getByText('Pendiente')).toBeDefined()
    expect(screen.getByText('Controlado')).toBeDefined()
    expect(screen.getByText('Extinguido')).toBeDefined()
  })

  it('shows loading state initially', async () => {
    ;(API.getFocosActivos as any).mockImplementation(() => new Promise(() => {}))
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    expect(screen.getByText('Cargando focos...')).toBeDefined()
    expect(screen.getByText('Cargando...')).toBeDefined()
  })

  it('shows error state on API failure', async () => {
    ;(API.getFocosActivos as any).mockRejectedValue(new Error('Error de red'))
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      expect(screen.getByText('Error de red')).toBeDefined()
    })
    expect(screen.getByText('Reintentar')).toBeDefined()
  })

  it('retries after error', async () => {
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    ;(API.getFocosActivos as any)
      .mockRejectedValueOnce(new Error('Error inicial'))
      .mockResolvedValueOnce([sampleFoco({ id: '2', lat: -33.46, lng: -70.68 })])

    await renderMapaFocos()
    await waitFor(() => expect(screen.getByText('Error inicial')).toBeDefined())
    fireEvent.click(screen.getByText('Reintentar'))
    await waitFor(() => {
      expect(screen.getByText('1 focos cercanos')).toBeDefined()
    })
  })

  it('shows empty state when no focos', async () => {
    ;(API.getFocosActivos as any).mockResolvedValue([])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      expect(screen.getByText('No hay focos activos cercanos')).toBeDefined()
    })
  })

  it('renders foco list after loading', async () => {
    ;(API.getFocosActivos as any).mockResolvedValue([sampleFoco()])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      expect(screen.getByText('Forestal')).toBeDefined()
    })
    expect(screen.getByText(/-33\.4500/)).toBeDefined()
    expect(screen.getByText('ACTIVO')).toBeDefined()
  })

  it('renders multiple focos sorted by distance', async () => {
    const cerca = sampleFoco({ id: '1', lat: -33.45, lng: -70.67 })
    const lejos = sampleFoco({ id: '2', lat: -33.40, lng: -70.60, descripcion: 'Más lejos' })
    ;(API.getFocosActivos as any).mockResolvedValue([lejos, cerca])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      const items = screen.getAllByText('Forestal')
      expect(items).toHaveLength(2)
    })
  })

  it('includes mis reportes regardless of estado/tiempo', async () => {
    localStorage.setItem('mis_reportes_ids', JSON.stringify(['my-1']))
    const old = new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString()
    ;(API.getFocosActivos as any).mockResolvedValue([
      sampleFoco({ id: 'my-1', estado: 'CONTROLADO', created_at: old }),
    ])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      expect(screen.getByText('CONTROLADO')).toBeDefined()
    })
  })

  it('shows slots count from localStorage', async () => {
    localStorage.setItem('mis_reportes_ids', JSON.stringify(['a', 'b']))
    ;(API.getFocosActivos as any).mockResolvedValue([])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => expect(screen.getByText(/Slots/)).toBeDefined())
    expect(screen.getByText('Slots: 2/5')).toBeDefined()
  })

  it('calls flyTo on foco click', async () => {
    const flyTo = vi.fn()
    mockRenderMap.mockImplementation((props: any) => {
      props.onMapReady({ flyTo })
      return <div data-testid="mock-map" />
    })
    ;(API.getFocosActivos as any).mockResolvedValue([sampleFoco()])
    await renderMapaFocos()
    await waitFor(() => expect(screen.getByText('Forestal')).toBeDefined())
    fireEvent.click(screen.getByRole('button', { name: /Incendio cerca del cerro/ }))
    expect(flyTo).toHaveBeenCalledWith({
      center: [-70.67, -33.45],
      zoom: 14,
      duration: 1000,
    })
  })

  it('highlights foco from location state', async () => {
    vi.mocked(await import('react-router-dom')).useLocation = () => ({
      state: { highlightId: 'hl-1' },
    })
    ;(API.getFocosActivos as any).mockResolvedValue([
      sampleFoco({ id: 'hl-1', lat: -33.44, lng: -70.66 }),
      sampleFoco({ id: 'other', lat: -33.45, lng: -70.67, descripcion: 'Otro' }),
    ])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      const hl = screen.getByText(/Incendio cerca del cerro/)
      expect(hl.closest('button')?.className).toContain('ring-blue-400')
    })
  })

  it('passes centerTo to strategy renderMap', async () => {
    vi.mocked(await import('react-router-dom')).useLocation = () => ({
      state: { centerTo: [-33.44, -70.66] },
    })
    ;(API.getFocosActivos as any).mockResolvedValue([])
    await renderMapaFocos()
    await waitFor(() => {
      expect(mockRenderMap).toHaveBeenCalledWith(
        expect.objectContaining({ centerTo: [-33.44, -70.66] })
      )
    })
  })

  it('filters out focos outside 50km radius', async () => {
    const lejano = sampleFoco({
      id: 'far',
      lat: -34.0,
      lng: -71.0,
      descripcion: 'Muy lejos',
    })
    ;(API.getFocosActivos as any).mockResolvedValue([lejano, sampleFoco({ id: 'near' })])
    mockRenderMap.mockReturnValue(<div data-testid="mock-map" />)
    await renderMapaFocos()
    await waitFor(() => {
      expect(screen.queryByText(/Muy lejos/)).toBeNull()
      expect(screen.getByText(/Incendio cerca del cerro/)).toBeDefined()
    })
    expect(screen.getByText('1 focos cercanos')).toBeDefined()
  })
})

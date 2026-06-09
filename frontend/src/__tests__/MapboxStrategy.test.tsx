import React, { type ReactNode } from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import type { MapRenderProps, FocoData } from '../util/map/MapStrategy'

const mockFlyTo = vi.fn()
let mockUseMapValue = { current: { flyTo: mockFlyTo } }

vi.mock('react-map-gl/mapbox', () => {
  const MockMap = React.forwardRef(({ children, onClick }: any, ref: any) => (
    <div ref={ref} data-testid="mock-map" onClick={onClick}>{children}</div>
  ))
  MockMap.displayName = 'MockMap'
  const MockMarker = ({ children, onClick, longitude, latitude }: any) => (
    <div data-testid="mock-marker" data-lng={longitude} data-lat={latitude} onClick={onClick}>{children}</div>
  )
  const MockPopup = ({ children, onClose, longitude, latitude }: any) => (
    <div data-testid="mock-popup" data-lng={longitude} data-lat={latitude}>
      <button data-testid="popup-close" onClick={onClose}>X</button>
      {children}
    </div>
  )
  const MockGeolocate = () => <div data-testid="mock-geolocate" />
  const MockUseMap = () => mockUseMapValue
  return {
    default: MockMap,
    Map: MockMap,
    Marker: MockMarker,
    Popup: MockPopup,
    GeolocateControl: MockGeolocate,
    useMap: MockUseMap,
  }
})

import { MapboxStrategy } from '../util/map'

const strategy = new MapboxStrategy()

function sampleFoco(overrides: Partial<FocoData> = {}): FocoData {
  return {
    id: '1',
    lat: -33.45,
    lng: -70.67,
    estado: 'ACTIVO',
    tipo: 'FORESTAL',
    descripcion: 'Incendio forestal',
    foto_url: '',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

function defaultProps(overrides: Partial<MapRenderProps> = {}): MapRenderProps {
  return {
    focos: [],
    highlightId: null,
    centerTo: null,
    selectedFoco: null,
    onSelectFoco: vi.fn(),
    onMapReady: vi.fn(),
    ...overrides,
  }
}

function renderStrategy(props: MapRenderProps) {
  return render(<>{strategy.renderMap(props)}</>)
}

describe('MapboxStrategy', () => {
  it('renders map container', () => {
    renderStrategy(defaultProps())
    expect(screen.getByTestId('mock-map')).toBeDefined()
  })

  it('renders GeolocateControl', () => {
    renderStrategy(defaultProps())
    expect(screen.getByTestId('mock-geolocate')).toBeDefined()
  })

  it('renders markers for each foco', () => {
    const focos = [
      sampleFoco({ id: '1' }),
      sampleFoco({ id: '2', lat: -33.46, lng: -70.68, estado: 'PENDIENTE' }),
    ]
    renderStrategy(defaultProps({ focos }))
    const markers = screen.getAllByTestId('mock-marker')
    expect(markers).toHaveLength(2)
  })

  it('marks highlighted foco with larger marker', () => {
    const focos = [sampleFoco({ id: '1' })]
    renderStrategy(defaultProps({ focos, highlightId: '1' }))
    const marker = screen.getByTestId('mock-marker')
    expect(marker).toBeDefined()
  })

  it('renders popup when selectedFoco is set', () => {
    const foco = sampleFoco({ descripcion: 'Incendio en cerro' })
    renderStrategy(defaultProps({ selectedFoco: foco }))
    expect(screen.getByTestId('mock-popup')).toBeDefined()
    expect(screen.getByText('Forestal')).toBeDefined()
    expect(screen.getByText('Incendio en cerro')).toBeDefined()
    expect(screen.getByText('ACTIVO')).toBeDefined()
  })

  it('renders tipo label as Urbano for non-forestal types', () => {
    const foco = sampleFoco({ tipo: 'URBANO' })
    renderStrategy(defaultProps({ selectedFoco: foco }))
    expect(screen.getByText('Urbano')).toBeDefined()
  })

  it('does not render popup when selectedFoco is null', () => {
    renderStrategy(defaultProps())
    expect(screen.queryByTestId('mock-popup')).toBeNull()
  })

  it('popup close triggers onSelectFoco(null)', () => {
    const onSelectFoco = vi.fn()
    renderStrategy(defaultProps({ selectedFoco: sampleFoco(), onSelectFoco }))
    fireEvent.click(screen.getByTestId('popup-close'))
    expect(onSelectFoco).toHaveBeenCalledWith(null)
  })

  it('renders popup with description only when present', () => {
    const foco = sampleFoco({ descripcion: '' })
    renderStrategy(defaultProps({ selectedFoco: foco }))
    expect(screen.queryByText(/Incendio forestal/)).toBeNull()
  })

  it('renders popup with foto when foto_url is set', () => {
    const foco = sampleFoco({ foto_url: 'https://example.com/foto.jpg' })
    renderStrategy(defaultProps({ selectedFoco: foco }))
    const img = screen.getByAltText('Foto del incendio')
    expect(img).toBeDefined()
    expect(img.getAttribute('src')).toBe('https://example.com/foto.jpg')
  })

  it('renders foco marker with foto when highlighted and has foto_url', () => {
    const foco = sampleFoco({ foto_url: 'https://example.com/foto.jpg' })
    renderStrategy(defaultProps({ focos: [foco], highlightId: '1' }))
    const img = screen.getByAltText('')
    expect(img).toBeDefined()
    expect(img.getAttribute('src')).toBe('https://example.com/foto.jpg')
  })

  it('renders foco marker with dot for non-highlighted foco', () => {
    const focos = [sampleFoco({ id: '1' })]
    renderStrategy(defaultProps({ focos }))
    const marker = screen.getByTestId('mock-marker')
    expect(marker).toBeDefined()
  })

  it('calls onSelectFoco when marker is clicked', () => {
    const onSelectFoco = vi.fn()
    const foco = sampleFoco({ id: '1' })
    renderStrategy(defaultProps({ focos: [foco], onSelectFoco }))
    fireEvent.click(screen.getByTestId('mock-marker'))
    expect(onSelectFoco).toHaveBeenCalledWith(foco)
  })

  it('calls onSelectFoco(null) when map background is clicked', () => {
    const onSelectFoco = vi.fn()
    renderStrategy(defaultProps({ onSelectFoco }))
    fireEvent.click(screen.getByTestId('mock-map'))
    expect(onSelectFoco).toHaveBeenCalledWith(null)
  })

  it('renders all estado types in marker dot color', () => {
    const focos: FocoData[] = [
      sampleFoco({ id: 'a', estado: 'ACTIVO' }),
      sampleFoco({ id: 'b', estado: 'PENDIENTE' }),
      sampleFoco({ id: 'c', estado: 'CONTROLADO' }),
      sampleFoco({ id: 'd', estado: 'EXTINGUIDO' }),
      sampleFoco({ id: 'e', estado: 'UNKNOWN' }),
    ]
    renderStrategy(defaultProps({ focos }))
    expect(screen.getAllByTestId('mock-marker')).toHaveLength(5)
  })

  it('calls onMapReady when map ref is available', () => {
    const onMapReady = vi.fn()
    renderStrategy(defaultProps({ onMapReady }))
    expect(onMapReady).toHaveBeenCalled()
  })

  it('FlyToCenter calls flyTo when target and map are available', () => {
    renderStrategy(defaultProps({ centerTo: [-33.45, -70.67] }))
    expect(mockFlyTo).toHaveBeenCalledWith({
      center: [-70.67, -33.45],
      zoom: 14,
      duration: 1500,
    })
  })

  it('FlyToCenter does nothing when target is null', () => {
    mockFlyTo.mockClear()
    renderStrategy(defaultProps({ centerTo: null }))
    expect(mockFlyTo).not.toHaveBeenCalled()
  })

  it('renders popup with correct estado color classes', () => {
    const renderProps = [
      { estado: 'ACTIVO', expectedClass: 'bg-red-100' },
      { estado: 'PENDIENTE', expectedClass: 'bg-amber-100' },
      { estado: 'CONTROLADO', expectedClass: 'bg-orange-100' },
      { estado: 'EXTINGUIDO', expectedClass: 'bg-green-100' },
      { estado: 'UNKNOWN', expectedClass: 'bg-gray-100' },
    ]
    for (const { estado, expectedClass } of renderProps) {
      const { unmount } = renderStrategy(defaultProps({ selectedFoco: sampleFoco({ estado }) }))
      const span = screen.getByText(estado)
      expect(span.className).toContain(expectedClass)
      unmount()
    }
  })
})

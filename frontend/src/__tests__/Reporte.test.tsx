import { describe, it, expect, vi, beforeEach, Mock } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate, useLocation: () => ({ state: null }) }
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

const mockAddToast = vi.fn()
vi.mock('../util/toast', async () => {
  const actual = await vi.importActual('../util/toast')
  return { ...actual, useToast: () => ({ addToast: mockAddToast }) }
})

vi.mock('../util/image', () => ({ compressImage: vi.fn() }))
vi.mock('../util/device', () => ({ getDeviceId: vi.fn(() => 'device-abc-123') }))

function createMockAuth(overrides = {}) {
  return {
    user: { user_id: '1', email: 'test@test.cl', nombre: 'Test', rol: 'VECINO' },
    token: 'valid-token',
    logout: vi.fn(),
    login: vi.fn(),
    ...overrides,
  }
}

let mockAuthValue = createMockAuth()
vi.mock('../App', () => ({
  useAuth: () => mockAuthValue,
}))

vi.mock('../api', () => ({
  API: { createReportAnonimo: vi.fn(), createReport: vi.fn(), uploadImage: vi.fn(), getFocosActivos: vi.fn() },
}))

import { API } from '../api'

beforeEach(() => {
  mockAuthValue = createMockAuth()
  vi.clearAllMocks()
  localStorage.clear()
})

async function renderReporte() {
  const Reporte = (await import('../pages/Reporte')).default
  return render(
    <MemoryRouter>
      <ToastProvider>
        <Reporte />
      </ToastProvider>
    </MemoryRouter>
  )
}

function mockGeolocation(success: boolean, data?: { lat: number; lng: number }) {
  const mockGeolocation = {
    getCurrentPosition: vi.fn().mockImplementation(
      (successCb: Function, errorCb: Function) => {
        if (success) {
          successCb({ coords: { latitude: data!.lat, longitude: data!.lng, accuracy: 10 } })
        } else {
          const err: any = { code: 1, message: 'Permission denied' }
          err.PERMISSION_DENIED = 1
          err.POSITION_UNAVAILABLE = 2
          err.TIMEOUT = 3
          errorCb(err)
        }
      }
    ),
  }
  Object.defineProperty(globalThis.navigator, 'geolocation', {
    value: mockGeolocation,
    writable: true,
    configurable: true,
  })
}

describe('Reporte Page', () => {
  it('renders form elements', async () => {
    await renderReporte()
    expect(screen.getByText('Reportar Incendio')).toBeDefined()
    expect(screen.getByText('Tipo de Incendio')).toBeDefined()
    expect(screen.getByText('Forestal')).toBeDefined()
    expect(screen.getByText('Urbano')).toBeDefined()
    expect(screen.getByText('Obtener Mi Ubicación')).toBeDefined()
    expect(screen.getByText('Tomar foto')).toBeDefined()
    expect(screen.getByText('Enviar Reporte')).toBeDefined()
  })

  it('shows anonymous banner when no user/token', async () => {
    mockAuthValue = createMockAuth({ user: null, token: null })
    await renderReporte()
    expect(screen.getByText('Reporte de Emergencia Rápido')).toBeDefined()
    expect(screen.getByText('Anónimo')).toBeDefined()
    expect(screen.getByText('¿Ya tienes cuenta? Inicia sesión aquí')).toBeDefined()
  })

  it('shows authenticated banner with user name', async () => {
    await renderReporte()
    expect(screen.getByText('Test')).toBeDefined()
    expect(screen.getByText('Cerrar')).toBeDefined()
  })

  it('toggles between forestal and urbano types', async () => {
    await renderReporte()
    const forestalBtn = screen.getByRole('button', { name: /Forestal/ })
    const urbanoBtn = screen.getByRole('button', { name: /Urbano/ })
    expect(forestalBtn.className).toContain('bg-fire-500')
    expect(urbanoBtn.className).toContain('bg-gray-200')
    fireEvent.click(urbanoBtn)
    expect(urbanoBtn.className).toContain('bg-fire-500')
    expect(forestalBtn.className).toContain('bg-gray-200')
  })

  it('obtains location on button click', async () => {
    mockGeolocation(true, { lat: -33.4489, lng: -70.6693 })
    await renderReporte()
    fireEvent.click(screen.getByText('Obtener Mi Ubicación'))
    await waitFor(() => {
      expect(screen.getByText(/-33\.4489/)).toBeDefined()
    })
    expect(screen.getByTestId('map-container')).toBeDefined()
  })

  it('shows GPS error when location fails', async () => {
    mockGeolocation(false)
    await renderReporte()
    fireEvent.click(screen.getByText('Obtener Mi Ubicación'))
    await waitFor(() => {
      expect(screen.getByText(/Permiso de ubicación denegado/)).toBeDefined()
    })
  })

  it('shows warning when submitting without location', async () => {
    await renderReporte()
    fireEvent.click(screen.getByText('Enviar Reporte'))
    expect(mockAddToast).toHaveBeenCalledWith('Obtén tu ubicación primero', 'warning')
  })

  it('submits report as anonymous user', async () => {
    mockAuthValue = createMockAuth({ user: null, token: null })
    API.createReportAnonimo = vi.fn().mockResolvedValue({ report_id: '123' })
    mockGeolocation(true, { lat: -33.45, lng: -70.67 })

    await renderReporte()
    fireEvent.click(screen.getByText('Obtener Mi Ubicación'))
    await waitFor(() => expect(screen.getByText(/✅ Ubicación/)).toBeDefined())

    fireEvent.click(screen.getByText('Enviar Reporte'))
    await waitFor(() => {
      expect(API.createReportAnonimo).toHaveBeenCalledWith({
        tipo: 'FORESTAL',
        latitud: -33.45,
        longitud: -70.67,
        descripcion: '',
        device_id: 'device-abc-123',
      })
    })
    expect(mockNavigate).toHaveBeenCalledWith('/confirmar', expect.objectContaining({
      state: expect.objectContaining({ reporte: { report_id: '123' }, isAnonymous: true }),
    }))
  })

  it('submits report as authenticated user', async () => {
    API.createReport = vi.fn().mockResolvedValue({ report_id: '456' })
    mockGeolocation(true, { lat: -33.46, lng: -70.68 })

    await renderReporte()
    fireEvent.click(screen.getByText('Obtener Mi Ubicación'))
    await waitFor(() => expect(screen.getByText(/✅ Ubicación/)).toBeDefined())

    const desc = screen.getByPlaceholderText('Describe lo que observas...')
    await userEvent.type(desc, 'Humo cerca del cerro')
    fireEvent.click(screen.getByText('Enviar Reporte'))
    await waitFor(() => {
      expect(API.createReport).toHaveBeenCalledWith('valid-token', {
        tipo: 'FORESTAL',
        latitud: -33.46,
        longitud: -70.68,
        descripcion: 'Humo cerca del cerro',
        user_id: '1',
      })
    })
    expect(mockNavigate).toHaveBeenCalledWith('/confirmar', expect.objectContaining({
      state: expect.objectContaining({ isAnonymous: false }),
    }))
  })

  it('shows error toast on submit failure', async () => {
    API.createReport = vi.fn().mockRejectedValue(new Error('Error del servidor'))
    mockGeolocation(true, { lat: -33.46, lng: -70.68 })

    await renderReporte()
    fireEvent.click(screen.getByText('Obtener Mi Ubicación'))
    await waitFor(() => expect(screen.getByText(/✅ Ubicación/)).toBeDefined())
    fireEvent.click(screen.getByText('Enviar Reporte'))
    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('Error del servidor', 'error')
    })
  })

  it('shows slot limit message when 5+ reports', async () => {
    localStorage.setItem('mis_reportes_ids', JSON.stringify(['a', 'b', 'c', 'd', 'e']))
    await renderReporte()
    expect(screen.getByText('Reportes activos: 5/5')).toBeDefined()
    expect(screen.getByText('Límite alcanzado')).toBeDefined()
    expect(screen.getByText(/Has alcanzado el límite máximo/)).toBeDefined()
    expect(screen.queryByText('Enviar Reporte')).toBeNull()
  })

  it('uploads photo and shows success label', async () => {
    const { compressImage } = await import('../util/image')
    ;(compressImage as Mock).mockResolvedValue(new Blob())
    API.uploadImage = vi.fn().mockResolvedValue('https://cdn.example.com/photo.jpg')

    await renderReporte()
    const input = screen.getByLabelText('Tomar foto')
    const file = new File(['fakedata'], 'foto.jpg', { type: 'image/jpeg' })
    await userEvent.upload(input, file)
    await waitFor(() => {
      expect(screen.getByText(/foto\.jpg/)).toBeDefined()
    })
    expect(API.uploadImage).toHaveBeenCalled()
  })

  it('shows error toast on photo upload failure', async () => {
    const { compressImage } = await import('../util/image')
    ;(compressImage as Mock).mockRejectedValue(new Error('Imagen muy grande'))
    await renderReporte()
    const input = screen.getByLabelText('Tomar foto')
    await userEvent.upload(input, new File(['x'], 'big.jpg', { type: 'image/jpeg' }))
    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith('Imagen muy grande', 'error')
    })
  })
})

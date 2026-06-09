import { describe, it, expect, vi, afterEach } from 'vitest'
import { render, screen, act, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
let mockUserAgent = ''

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

afterEach(() => {
  vi.restoreAllMocks()
  mockUserAgent = ''
})

describe('RedireccionQR Page', () => {
  it('shows spinner and redirects on non-Android', async () => {
    vi.useFakeTimers()
    const RedireccionQr = (await import('../pages/RedireccionQr')).default
    render(<MemoryRouter><RedireccionQr /></MemoryRouter>)
    expect(screen.getByText('Redirigiendo...')).toBeDefined()
    act(() => { vi.advanceTimersByTime(0) })
    expect(mockNavigate).toHaveBeenCalledWith('/login?utm_source=afiche_municipal&utm_medium=qr', { replace: true })
    vi.useRealTimers()
  })

  it('shows Android message', async () => {
    mockUserAgent = 'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36'
    Object.defineProperty(navigator, 'userAgent', { get: () => mockUserAgent, configurable: true })

    const RedireccionQr = (await import('../pages/RedireccionQr')).default
    render(<MemoryRouter><RedireccionQr /></MemoryRouter>)
    expect(screen.getByText('Abriendo Chrome...')).toBeDefined()
  })

  it('renders fallback link on Android', async () => {
    mockUserAgent = 'Mozilla/5.0 (Linux; Android 14)'
    Object.defineProperty(navigator, 'userAgent', { get: () => mockUserAgent, configurable: true })
    const RedireccionQr = (await import('../pages/RedireccionQr')).default
    render(<MemoryRouter><RedireccionQr /></MemoryRouter>)
    const link = screen.getByText('presiona aquí')
    expect(link).toBeDefined()
    fireEvent.click(link)
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true })
  })
})

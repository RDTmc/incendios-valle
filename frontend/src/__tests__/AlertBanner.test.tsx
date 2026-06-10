import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'

const mockFetch = vi.fn()

const mockAlerts = [
  { id: 1, alert_type: 'CRITICO', message: 'Incendio en cerro', report_id: 'r1', latitud: -33.45, longitud: -70.67, source: 'web', read: false, created_at: '2025-01-01T00:00:00Z' },
  { id: 2, alert_type: 'INFO', message: 'Monitoreo normal', report_id: 'r2', latitud: -33.46, longitud: -70.68, source: 'web', read: false, created_at: '2025-01-01T01:00:00Z' },
]

let intervalCallback: (() => void) | null = null
const realSetInterval = globalThis.setInterval
const realClearInterval = globalThis.clearInterval

beforeEach(() => {
  mockFetch.mockReset()
  intervalCallback = null
  globalThis.fetch = mockFetch as any
  globalThis.setInterval = vi.fn(((cb: () => void, _ms: number) => {
    intervalCallback = cb
    return 123
  }) as any) as any
  globalThis.clearInterval = vi.fn() as any
})

afterEach(() => {
  globalThis.fetch = undefined as any
  globalThis.setInterval = realSetInterval
  globalThis.clearInterval = realClearInterval
})

function mockSuccess(data: any) {
  mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(data) })
}

describe('AlertBanner', () => {
  it('renders null when no alerts', async () => {
    mockSuccess([])
    const AlertBanner = (await import('../components/AlertBanner')).default
    const { container } = render(<AlertBanner />)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
      expect(container.innerHTML).toBe('')
    })
  })

  it('renders alerts from API', async () => {
    mockSuccess(mockAlerts)
    const AlertBanner = (await import('../components/AlertBanner')).default
    render(<AlertBanner />)
    await waitFor(() => {
      expect(screen.getByText('CRITICO')).toBeDefined()
      expect(screen.getByText('Incendio en cerro')).toBeDefined()
    })
  })

  it('renders alert with correct role', async () => {
    mockSuccess(mockAlerts)
    const AlertBanner = (await import('../components/AlertBanner')).default
    render(<AlertBanner />)
    await waitFor(() => {
      expect(screen.getAllByRole('alert')).toHaveLength(2)
    })
  })

  it('dismiss removes alert and calls PUT', async () => {
    mockSuccess(mockAlerts)
    const AlertBanner = (await import('../components/AlertBanner')).default
    render(<AlertBanner />)
    await waitFor(() => expect(screen.getByText('CRITICO')).toBeDefined())

    const dismissBtns = screen.getAllByRole('button')
    fireEvent.click(dismissBtns[0])

    expect(screen.queryByText('Incendio en cerro')).toBeNull()
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/alerts/1/read'),
      expect.objectContaining({ method: 'PUT' })
    )
  })

  it('sets up polling interval', async () => {
    mockSuccess(mockAlerts)
    const AlertBanner = (await import('../components/AlertBanner')).default
    render(<AlertBanner />)
    await waitFor(() => expect(mockFetch).toHaveBeenCalled())
    expect(intervalCallback).not.toBeNull()
  })

  it('silently fails on fetch error', async () => {
    mockFetch.mockRejectedValue(new Error('Network error'))
    const AlertBanner = (await import('../components/AlertBanner')).default
    const { container } = render(<AlertBanner />)
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled()
      expect(container.innerHTML).toBe('')
    })
  })
})

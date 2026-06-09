import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import OfflineBanner from '../components/OfflineBanner'

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('OfflineBanner', () => {
  it('should not render when online', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })
    const { container } = render(<OfflineBanner />)
    expect(container.innerHTML).toBe('')
  })

  it('should render when offline', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    render(<OfflineBanner />)
    expect(screen.getByText(/Sin conexión/)).toBeDefined()
  })

  it('should react to offline event', () => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })
    const { container } = render(<OfflineBanner />)
    expect(container.innerHTML).toBe('')
    act(() => { window.dispatchEvent(new Event('offline')) })
    expect(screen.getByText(/Sin conexión/)).toBeDefined()
  })

  it('should react to online event', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    render(<OfflineBanner />)
    expect(screen.getByText(/Sin conexión/)).toBeDefined()
    act(() => { window.dispatchEvent(new Event('online')) })
    expect(screen.queryByText(/Sin conexión/)).toBeNull()
  })

  it('should clean up event listeners on unmount', () => {
    const removeSpy = vi.spyOn(window, 'removeEventListener')
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })
    const { unmount } = render(<OfflineBanner />)
    unmount()
    expect(removeSpy).toHaveBeenCalledWith('online', expect.any(Function))
    expect(removeSpy).toHaveBeenCalledWith('offline', expect.any(Function))
  })
})

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import ToastContainer from '../components/Toast'
import { ToastProvider, useToast } from '../util/toast'

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

function TestHarness() {
  const { addToast } = useToast()
  return (
    <div>
      <button onClick={() => addToast('test message', 'success')}>Add Success</button>
      <button onClick={() => addToast('error message', 'error')}>Add Error</button>
      <button onClick={() => addToast('warning', 'warning', 0)}>Add NoAuto</button>
    </div>
  )
}

function renderWithProvider(ui: React.ReactElement) {
  return render(
    <ToastProvider>
      <ToastContainer />
      {ui}
    </ToastProvider>
  )
}

describe('ToastProvider', () => {
  it('throws when useToast is called outside provider', () => {
    function Broken() {
      useToast()
      return null
    }
    expect(() => render(<Broken />)).toThrow('useToast must be used within ToastProvider')
  })

  it('renders children', () => {
    render(<ToastProvider><div>child</div></ToastProvider>)
    expect(screen.getByText('child')).toBeDefined()
  })

  it('adds a toast and displays it', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    expect(screen.getByText('test message')).toBeDefined()
    expect(screen.getByText('✓')).toBeDefined()
  })

  it('adds multiple toasts', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    fireEvent.click(screen.getByText('Add Error'))
    expect(screen.getByText('test message')).toBeDefined()
    expect(screen.getByText('error message')).toBeDefined()
  })

  it('removes toast on close button click', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    expect(screen.getByText('test message')).toBeDefined()
    fireEvent.click(screen.getByLabelText('Cerrar'))
    expect(screen.queryByText('test message')).toBeNull()
  })

  it('auto-removes toast after duration', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    expect(screen.getByText('test message')).toBeDefined()

    act(() => { vi.advanceTimersByTime(4000) })
    expect(screen.queryByText('test message')).toBeNull()
  })

  it('does not auto-remove when duration is 0', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add NoAuto'))
    expect(screen.getByText('warning')).toBeDefined()

    act(() => { vi.advanceTimersByTime(5000) })
    expect(screen.getByText('warning')).toBeDefined()
  })

  it('renders correct icon per type', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    const alerts = screen.getAllByRole('alert')
    expect(alerts[0].textContent).toContain('✓')
  })
})

describe('ToastContainer', () => {
  it('returns null when there are no toasts', () => {
    const { container } = render(
      <ToastProvider>
        <ToastContainer />
      </ToastProvider>
    )
    expect(container.innerHTML).toBe('')
  })

  it('renders multiple toasts with role alert', () => {
    renderWithProvider(<TestHarness />)
    fireEvent.click(screen.getByText('Add Success'))
    fireEvent.click(screen.getByText('Add Error'))
    const alerts = screen.getAllByRole('alert')
    expect(alerts).toHaveLength(2)
  })
})

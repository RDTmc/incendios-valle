import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import ErrorBoundary from '../components/ErrorBoundary'

function Bomb() {
  throw new Error('Test error')
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('ErrorBoundary', () => {
  it('should render children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Contenido normal</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Contenido normal')).toBeDefined()
  })

  it('should show error UI when child throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>
    )
    expect(screen.getByText('Algo salió mal')).toBeDefined()
    expect(screen.getByText('Ocurrió un error inesperado. Por favor intenta de nuevo.')).toBeDefined()
    expect(screen.getByText('Reintentar')).toBeDefined()
  })

  it('should reload page on retry click', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    const reload = vi.fn()
    Object.defineProperty(window, 'location', { value: { reload }, writable: true })

    render(
      <ErrorBoundary>
        <Bomb />
      </ErrorBoundary>
    )
    screen.getByText('Reintentar').click()
    expect(reload).toHaveBeenCalled()
  })
})

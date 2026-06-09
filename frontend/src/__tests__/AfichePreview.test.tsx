import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

it('renders afiche content', async () => {
  const AfichePreview = (await import('../pages/AfichePreview')).default
  render(<AfichePreview />)
  expect(screen.getByText('Incendios Valle del Sol')).toBeDefined()
  expect(screen.getByText('Reporte Ciudadano de Emergencia')).toBeDefined()
  expect(screen.getByText(/Escanea y reporta en 30 segundos/)).toBeDefined()
  expect(screen.getByText(/Si tu telefono lee el codigo como texto/)).toBeDefined()
})

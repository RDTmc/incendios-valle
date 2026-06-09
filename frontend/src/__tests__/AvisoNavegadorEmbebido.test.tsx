import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

const mockDetectar = vi.fn()
const mockInstalable = vi.fn()
vi.mock('../util/navegador', () => ({
  detectarNavegadorEmbebido: () => mockDetectar(),
  esNavegadorInstalable: () => mockInstalable(),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

async function renderComponent() {
  const Aviso = (await import('../components/AvisoNavegadorEmbebido')).default
  return render(<Aviso />)
}

describe('AvisoNavegadorEmbebido', () => {
  it('renders null when no embebido detected', async () => {
    mockDetectar.mockReturnValue(null)
    mockInstalable.mockReturnValue(false)
    const { container } = await renderComponent()
    expect(container.innerHTML).toBe('')
  })

  it('renders null when PWA is already installed', async () => {
    mockDetectar.mockReturnValue('Facebook')
    mockInstalable.mockReturnValue(true)
    const { container } = await renderComponent()
    expect(container.innerHTML).toBe('')
  })

  it('shows warning when embebido detected and not installed', async () => {
    mockDetectar.mockReturnValue('Facebook')
    mockInstalable.mockReturnValue(false)
    await renderComponent()
    expect(screen.getByText(/Detectamos que estás usando/)).toBeDefined()
    expect(screen.getByText('Facebook')).toBeDefined()
  })

  it('dismisses on close button click', async () => {
    mockDetectar.mockReturnValue('Instagram')
    mockInstalable.mockReturnValue(false)
    await renderComponent()
    const closeBtn = screen.getByLabelText('Cerrar')
    fireEvent.click(closeBtn)
    expect(screen.queryByText(/Detectamos que estás usando/)).toBeNull()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../api', () => ({
  API: { register: vi.fn() }
}))

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <BrowserRouter>
      <ToastProvider>
        {ui}
      </ToastProvider>
    </BrowserRouter>
  )
}

const submitBtn = () => screen.getByRole('button', { name: 'Crear Cuenta' })
const submitForm = () => submitBtn().closest('form')!

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Registro Page', () => {
  it('renders the registration form', async () => {
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)
    expect(screen.getByRole('heading', { name: 'Crear Cuenta' })).toBeDefined()
    expect(screen.getByText('Regístrate para reportar incendios')).toBeDefined()
    expect(screen.getByPlaceholderText('Tu nombre')).toBeDefined()
    expect(screen.getByPlaceholderText('correo@ejemplo.com')).toBeDefined()
    expect(screen.getByPlaceholderText('Mínimo 6 caracteres')).toBeDefined()
    expect(screen.getByPlaceholderText('Repite la contraseña')).toBeDefined()
    expect(submitBtn()).toBeDefined()
  })

  it('shows error when submitting empty form', async () => {
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)
    fireEvent.submit(submitForm())
    await waitFor(() => {
      expect(screen.getByText('Ingresa tu nombre')).toBeDefined()
    })
  })

  it('shows error when password is too short', async () => {
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)
    await userEvent.type(screen.getByPlaceholderText('Tu nombre'), 'Juan')
    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'j@j.cl')
    await userEvent.type(screen.getByPlaceholderText('Mínimo 6 caracteres'), '123')
    await userEvent.type(screen.getByPlaceholderText('Repite la contraseña'), '123')
    fireEvent.submit(submitForm())
    await waitFor(() => {
      expect(screen.getByText('La contraseña debe tener al menos 6 caracteres')).toBeDefined()
    })
  })

  it('shows error when passwords do not match', async () => {
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)
    await userEvent.type(screen.getByPlaceholderText('Tu nombre'), 'Juan')
    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'j@j.cl')
    await userEvent.type(screen.getByPlaceholderText('Mínimo 6 caracteres'), '123456')
    await userEvent.type(screen.getByPlaceholderText('Repite la contraseña'), '654321')
    fireEvent.submit(submitForm())
    await waitFor(() => {
      expect(screen.getByText('Las contraseñas no coinciden')).toBeDefined()
    })
  })

  it('calls API.register on valid submission', async () => {
    const { API } = await import('../api')
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)

    await userEvent.type(screen.getByPlaceholderText('Tu nombre'), 'Juan Pérez')
    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'juan@test.cl')
    await userEvent.type(screen.getByPlaceholderText('Mínimo 6 caracteres'), 'password123')
    await userEvent.type(screen.getByPlaceholderText('Repite la contraseña'), 'password123')
    fireEvent.submit(submitForm())

    await waitFor(() => {
      expect(API.register).toHaveBeenCalledWith('juan@test.cl', 'password123', 'Juan Pérez')
    })
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('shows error on registration failure', async () => {
    const { API } = await import('../api')
    ;(API.register as any).mockRejectedValue(new Error('Email ya registrado'))
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)

    await userEvent.type(screen.getByPlaceholderText('Tu nombre'), 'Juan')
    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'dup@test.cl')
    await userEvent.type(screen.getByPlaceholderText('Mínimo 6 caracteres'), 'password123')
    await userEvent.type(screen.getByPlaceholderText('Repite la contraseña'), 'password123')
    fireEvent.submit(submitForm())

    await waitFor(() => {
      expect(screen.getByText('Email ya registrado')).toBeDefined()
    })
  })

  it('has link to login page', async () => {
    const Registro = (await import('../pages/Registro')).default
    renderWithProviders(<Registro />)
    expect(screen.getByText('¿Ya tienes cuenta? Inicia sesión')).toBeDefined()
  })
})

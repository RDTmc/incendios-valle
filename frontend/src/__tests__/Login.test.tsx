import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockSetAuthFrom2FA = vi.fn()
const mockAPILogin = vi.fn()

vi.mock('../App', () => ({
  useAuth: () => ({
    user: null,
    token: null,
    login: vi.fn(),
    logout: vi.fn(),
    setAuthFrom2FA: mockSetAuthFrom2FA
  })
}))

vi.mock('../api', () => ({
  API: { login: mockAPILogin }
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

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('Login Page', () => {
  it('should render the login form', async () => {
    const Login = (await import('../pages/Login')).default
    renderWithProviders(<Login />)

    expect(screen.getByText('Incendios Valle del Sol')).toBeDefined()
    expect(screen.getByText('Sistema de Gestión de Emergencias')).toBeDefined()
    expect(screen.getByText('Iniciar Sesión')).toBeDefined()
    expect(screen.getByText('Reportar Emergencia Rápida')).toBeDefined()
  })

  it('should have email and password inputs', async () => {
    const Login = (await import('../pages/Login')).default
    renderWithProviders(<Login />)

    expect(screen.getByPlaceholderText('correo@ejemplo.com')).toBeDefined()
    expect(screen.getByPlaceholderText('••••••••')).toBeDefined()
  })

  it('should show password toggle button', async () => {
    const Login = (await import('../pages/Login')).default
    renderWithProviders(<Login />)

    const passwordInput = screen.getByPlaceholderText('••••••••')
    expect(passwordInput).toHaveAttribute('type', 'password')

    const toggleButton = document.querySelector('button[type="button"]')
    expect(toggleButton).toBeDefined()
  })

  it('should have a link to anonymous reporting', async () => {
    const Login = (await import('../pages/Login')).default
    renderWithProviders(<Login />)

    const anonymousButton = screen.getByText('Reportar Emergencia Rápida')
    expect(anonymousButton).toBeDefined()
  })

  it('should have a registration link', async () => {
    const Login = (await import('../pages/Login')).default
    renderWithProviders(<Login />)

    expect(screen.getByText('¿No tienes cuenta? Regístrate aquí')).toBeDefined()
  })

  it('should submit form with email and password', async () => {
    const Login = (await import('../pages/Login')).default
    mockAPILogin.mockResolvedValue({ token: 'test-token', user: { id: 1, name: 'Test', email: 'user@example.com' } })
    renderWithProviders(<Login />)

    const emailInput = screen.getByPlaceholderText('correo@ejemplo.com')
    const passwordInput = screen.getByPlaceholderText('••••••••')
    const submitButton = screen.getByText('Iniciar Sesión')

    await userEvent.type(emailInput, 'user@example.com')
    await userEvent.type(passwordInput, 'password123')
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockAPILogin).toHaveBeenCalledWith('user@example.com', 'password123')
      expect(mockSetAuthFrom2FA).toHaveBeenCalledWith('test-token', { id: 1, name: 'Test', email: 'user@example.com' })
    })
  })
})

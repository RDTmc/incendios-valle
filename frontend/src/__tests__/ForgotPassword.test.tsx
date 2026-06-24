import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockAPIForgot = vi.fn()
const mockAPIReset = vi.fn()

vi.mock('../api', () => ({
  API: {
    forgotPassword: mockAPIForgot,
    resetPassword: mockAPIReset,
  }
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

describe('ForgotPassword Page', () => {
  it('should show email form on step 1', async () => {
    const ForgotPassword = (await import('../pages/ForgotPassword')).default
    renderWithProviders(<ForgotPassword />)

    expect(screen.getByText('Recuperar Contraseña')).toBeDefined()
    expect(screen.getByText('Enviar Código de Verificación')).toBeDefined()
    expect(screen.getByPlaceholderText('correo@ejemplo.com')).toBeDefined()
  })

  it('should send OTP and show reset form on step 2', async () => {
    const ForgotPassword = (await import('../pages/ForgotPassword')).default
    mockAPIForgot.mockResolvedValue({ message: 'Código de verificación enviado al correo' })
    renderWithProviders(<ForgotPassword />)

    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'user@test.cl')
    fireEvent.click(screen.getByText('Enviar Código de Verificación'))

    await waitFor(() => {
      expect(mockAPIForgot).toHaveBeenCalledWith('user@test.cl')
      expect(screen.getByText('Restablecer Contraseña')).toBeDefined()
    })
  })

  it('should show success after valid OTP and matching passwords', async () => {
    const ForgotPassword = (await import('../pages/ForgotPassword')).default
    mockAPIForgot.mockResolvedValue({ message: 'Código enviado' })
    mockAPIReset.mockResolvedValue({ message: 'Contraseña actualizada correctamente' })
    renderWithProviders(<ForgotPassword />)

    await userEvent.type(screen.getByPlaceholderText('correo@ejemplo.com'), 'user@test.cl')
    fireEvent.click(screen.getByText('Enviar Código de Verificación'))

    await waitFor(() => {
      expect(screen.getByText('Restablecer Contraseña')).toBeDefined()
    })

    const otpInputs = document.querySelectorAll('input[inputMode="numeric"]')
    otpInputs.forEach((input, i) => {
      fireEvent.change(input, { target: { value: String(i + 1) } })
    })

    const passwordInputs = screen.getAllByPlaceholderText(/Mínimo 6 caracteres|Repite la/)
    await userEvent.type(passwordInputs[0], 'NewPass123')
    await userEvent.type(passwordInputs[1], 'NewPass123')

    fireEvent.click(screen.getByText('Restablecer Contraseña'))

    await waitFor(() => {
      expect(mockAPIReset).toHaveBeenCalledWith('user@test.cl', '123456', 'NewPass123', undefined)
      expect(screen.getByText('Contraseña actualizada')).toBeDefined()
    })
  })
})

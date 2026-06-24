import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '../util/toast'

const mockLogout = vi.fn()
const mockNavigate = vi.fn()

const mockAPIGetUsers = vi.fn()
const mockAPIGetReports = vi.fn()
const mockAPIUpdateStatus = vi.fn()
const mockAPIGetAuditLog = vi.fn()
const mockAPIGetNotifications = vi.fn()

vi.mock('../App', () => ({
  useAuth: () => ({
    user: { email: 'admin@test.cl', rol: 'ADMIN', nombre: 'Admin' },
    token: 'test-admin-token',
    logout: mockLogout
  })
}))

vi.mock('../api', () => ({
  API: {
    adminGetUsers: mockAPIGetUsers,
    adminGetReports: mockAPIGetReports,
    updateReportStatus: mockAPIUpdateStatus,
    getAuditLog: mockAPIGetAuditLog,
    adminGetNotifications: mockAPIGetNotifications,
  }
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate
  }
})

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
  mockAPIGetUsers.mockResolvedValue({ users: [], total: 0 })
  mockAPIGetReports.mockResolvedValue({ reports: [], total: 0 })
  mockAPIGetAuditLog.mockResolvedValue([])
  mockAPIGetNotifications.mockResolvedValue([])
})

describe('AdminPage Reports Tab', () => {
  it('should render reports tab with data', async () => {
    mockAPIGetReports.mockResolvedValue({
      reports: [
        { report_id: 'r1', user_id: 'u1', tipo: 'FORESTAL', latitud: -33.45, longitud: -70.67, descripcion: 'Incendio en cerro', foto_url: '', estado: 'ACTIVO', created_at: '2026-06-20T12:00:00' },
        { report_id: 'r2', user_id: 'u2', tipo: 'URBANO', latitud: -33.46, longitud: -70.68, descripcion: 'Casa en llamas', foto_url: '', estado: 'PENDIENTE', created_at: '2026-06-20T13:00:00' },
      ],
      total: 2
    })

    const AdminPage = (await import('../pages/AdminPage')).default
    renderWithProviders(<AdminPage />)

    await waitFor(() => {
      const buttons = document.querySelectorAll('button')
      const reportBtn = Array.from(buttons).find(b => b.textContent?.includes('Reportes'))
      expect(reportBtn).toBeDefined()
    })

    const buttons = document.querySelectorAll('button')
    const reportBtn = Array.from(buttons).find(b => b.textContent?.includes('Reportes'))
    fireEvent.click(reportBtn!)

    await waitFor(() => {
      expect(screen.getByText('Incendio en cerro')).toBeDefined()
      expect(screen.getByText('Casa en llamas')).toBeDefined()
    })
  })

  it('should call updateReportStatus when estado changes in dropdown', async () => {
    mockAPIGetReports.mockResolvedValue({
      reports: [
        { report_id: 'r1', user_id: 'u1', tipo: 'FORESTAL', latitud: -33.45, longitud: -70.67, descripcion: 'Test', foto_url: '', estado: 'PENDIENTE', created_at: '2026-06-20T12:00:00' },
      ],
      total: 1
    })
    mockAPIUpdateStatus.mockResolvedValue({ status: 'updated', report_id: 'r1', estado: 'ACTIVO' })

    const AdminPage = (await import('../pages/AdminPage')).default
    renderWithProviders(<AdminPage />)

    await waitFor(() => {
      const buttons = document.querySelectorAll('button')
      const reportBtn = Array.from(buttons).find(b => b.textContent?.includes('Reportes'))
      expect(reportBtn).toBeDefined()
    })

    const buttons = document.querySelectorAll('button')
    const reportBtn = Array.from(buttons).find(b => b.textContent?.includes('Reportes'))
    fireEvent.click(reportBtn!)

    await waitFor(() => {
      expect(screen.getByText('Test')).toBeDefined()
    })

    const select = screen.getByDisplayValue('PENDIENTE')
    fireEvent.change(select, { target: { value: 'ACTIVO' } })

    await waitFor(() => {
      expect(mockAPIUpdateStatus).toHaveBeenCalledWith('test-admin-token', 'r1', 'ACTIVO')
    })
  })
})

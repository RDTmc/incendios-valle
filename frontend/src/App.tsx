import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import { API } from './api'

// Pages
import Login from './pages/Login'
import Reporte from './pages/Reporte'
import Confirmacion from './pages/Confirmacion'
import MapaFocos from './pages/MapaFocos'
import Historial from './pages/Historial'

// Context
interface AuthContextType {
  user: { user_id: string; email: string; rol: string; nombre: string } | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

// Componente Guard para rutas protegidas por rol
const ProtectedRoute = ({ children, allowedRoles }: { children: React.ReactNode; allowedRoles?: string[] }) => {
  const { user, token } = useAuth()

  if (!token || !user) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && !allowedRoles.includes(user.rol)) {
    // Si el usuario no tiene el rol permitido, redirigir según su rol
    if (user.rol === 'ADMIN') {
      return <Navigate to="/admin" replace />
    }
    return <Navigate to="/vecino" replace />
  }

  return <>{children}</>
}

function App() {
  // P3-1 + P3-5: Initialize from localStorage con role
  const [user, setUser] = useState<{ user_id: string; email: string; rol: string; nombre: string } | null>(() => {
    const saved = localStorage.getItem('incendios_user')
    return saved ? JSON.parse(saved) : null
  })
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('incendios_token')
  })

  // P3-1 + P3-5: Sync to localStorage cuando cambia auth state
  useEffect(() => {
    if (user) {
      localStorage.setItem('incendios_user', JSON.stringify(user))
    } else {
      localStorage.removeItem('incendios_user')
    }
  }, [user])

  useEffect(() => {
    if (token) {
      localStorage.setItem('incendios_token', token)
    } else {
      localStorage.removeItem('incendios_token')
    }
  }, [token])

  const login = async (email: string, password: string) => {
    const response = await API.login(email, password)
    setToken(response.token)
    setUser({
      user_id: response.user.user_id,
      email: response.user.email,
      rol: response.user.rol,
      nombre: response.user.nombre || ''
    })
  }

  const logout = () => {
    setUser(null)
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      <BrowserRouter>
        <Routes>
          {/* Login: redirige si ya hay sesión */}
          <Route path="/login" element={user ? <Navigate to={user.rol === 'ADMIN' ? '/admin' : '/reporte'} /> : <Login />} />
          
          {/* Rutas Admin */}
          <Route path="/admin" element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <Historial />
            </ProtectedRoute>
          } />
          
          {/* Rutas Vecino */}
          <Route path="/reporte" element={
            <ProtectedRoute allowedRoles={['VECINO']}>
              <Reporte />
            </ProtectedRoute>
          } />
          <Route path="/confirmar" element={
            <ProtectedRoute allowedRoles={['VECINO']}>
              <Confirmacion />
            </ProtectedRoute>
          } />
          <Route path="/mapa" element={<MapaFocos />} />
          <Route path="/historial" element={
            <ProtectedRoute allowedRoles={['VECINO']}>
              <Historial />
            </ProtectedRoute>
          } />
          
          {/* Rutas genéricas */}
          <Route path="/vecino" element={<Navigate to="/reporte" replace />} />
          <Route path="/" element={<Navigate to={user ? (user.rol === 'ADMIN' ? '/admin' : '/reporte') : '/login'} replace />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}

export default App

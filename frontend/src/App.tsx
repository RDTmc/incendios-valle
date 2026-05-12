import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, createContext, useContext } from 'react'
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

function App() {
  const [user, setUser] = useState<{ user_id: string; email: string; rol: string; nombre: string } | null>(null)
  const [token, setToken] = useState<string | null>(null)

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
          <Route path="/login" element={<Login />} />
          <Route path="/reporte" element={user ? <Reporte /> : <Navigate to="/login" />} />
          <Route path="/confirmar" element={user ? <Confirmacion /> : <Navigate to="/login" />} />
          <Route path="/mapa" element={<MapaFocos />} />
          <Route path="/historial" element={user ? <Historial /> : <Navigate to="/login" />} />
          <Route path="/" element={<Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </AuthContext.Provider>
  )
}

export default App
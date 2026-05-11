import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useState, createContext, useContext } from 'react'

// Pages
import Login from './pages/Login'
import Reporte from './pages/Reporte'
import Confirmacion from './pages/Confirmacion'
import MapaFocos from './pages/MapaFocos'
import Historial from './pages/Historial'

// Context
interface AuthContextType {
  user: { id: string; email: string; rol: string } | null
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
  const [user, setUser] = useState<{ id: string; email: string; rol: string } | null>(null)

  const login = async (email: string, password: string) => {
    // TODO: Implementar login con Lambda ms-usuarios
    setUser({ id: '1', email, rol: 'VECINO' })
  }

  const logout = () => {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
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
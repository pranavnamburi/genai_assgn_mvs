import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import BusDashboard from './pages/BusDashboard'
import ManageRoute from './pages/ManageRoute'
import './App.css'

function Navigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const currentPage = location.pathname === '/dashboard' ? 'dashboard' : 'routes'

  return (
    <div className="flex gap-2 p-4 bg-white border-b border-border">
      <button
        onClick={() => navigate('/dashboard')}
        className={`px-4 py-2 rounded font-medium ${
          currentPage === "dashboard" ? "bg-blue-600 text-white" : "bg-muted text-foreground hover:bg-muted/80"
        }`}
      >
        Bus Dashboard
      </button>
      <button
        onClick={() => navigate('/manage-routes')}
        className={`px-4 py-2 rounded font-medium ${
          currentPage === "routes" ? "bg-blue-600 text-white" : "bg-muted text-foreground hover:bg-muted/80"
        }`}
      >
        Manage Route
      </button>
    </div>
  )
}

function AppContent() {
  return (
    <div>
      <Navigation />
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<BusDashboard />} />
        <Route path="/manage-routes" element={<ManageRoute />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navigation from './components/Navigation'
import DashboardPage from './pages/DashboardPage'
import SymbolDetailPage from './pages/SymbolDetailPage'

export default function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/symbol/:symbol" element={<SymbolDetailPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

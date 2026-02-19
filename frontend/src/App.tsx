import { Routes, Route, NavLink } from 'react-router-dom'
import Layout from './Layout'
import Dashboard from './pages/Dashboard'
import Inventory from './pages/Inventory'
import Requirements from './pages/Requirements'
import Coverage from './pages/Coverage'
import Reports from './pages/Reports'
import AIReport from './pages/AIReport'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/requirements" element={<Requirements />} />
        <Route path="/coverage" element={<Coverage />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/ai-report" element={<AIReport />} />
      </Routes>
    </Layout>
  )
}

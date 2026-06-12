import { Routes, Route, Navigate } from 'react-router-dom'
import { Box, Container } from '@mui/material'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Companies from './pages/Companies'
import CompanyDetail from './pages/CompanyDetail'
import Search from './pages/Search'
import Monitoring from './pages/Monitoring'
import Industry from './pages/Industry'

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Container maxWidth="xl" sx={{ py: 3 }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/companies/:id" element={<CompanyDetail />} />
            <Route path="/search" element={<Search />} />
            <Route path="/monitoring" element={<Monitoring />} />
            <Route path="/industry" element={<Industry />} />
          </Routes>
        </Container>
      </Layout>
    </Box>
  )
}

export default App
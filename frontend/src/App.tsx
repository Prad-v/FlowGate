import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Templates from './pages/Templates'
import Deployments from './pages/Deployments'
import LogTransformer from './pages/LogTransformer'
import AgentManagement from './pages/AgentManagement'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/deployments" element={<Deployments />} />
          <Route path="/log-transformer" element={<LogTransformer />} />
          <Route path="/agents" element={<AgentManagement />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App

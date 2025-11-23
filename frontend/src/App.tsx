import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Templates from './pages/Templates'
import TemplateDetail from './pages/TemplateDetail'
import Deployments from './pages/Deployments'
import LogTransformer from './pages/LogTransformer'
import AgentManagement from './pages/AgentManagement'
import AgentDetails from './pages/AgentDetails'
import OpAMPConfigManagement from './pages/OpAMPConfigManagement'
import CreateConfigDeployment from './pages/CreateConfigDeployment'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/templates/:id" element={<TemplateDetail />} />
          <Route path="/deployments" element={<Deployments />} />
          <Route path="/log-transformer" element={<LogTransformer />} />
          <Route path="/agents" element={<AgentManagement />} />
          <Route path="/agents/:instanceId" element={<AgentDetails />} />
          <Route path="/opamp-config" element={<OpAMPConfigManagement />} />
          <Route path="/opamp-config/create" element={<CreateConfigDeployment />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App

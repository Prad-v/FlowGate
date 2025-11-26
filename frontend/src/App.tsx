import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './components/Login'
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
import ThreatManagement from './pages/ThreatManagement'
import AccessGovernance from './pages/AccessGovernance'
import Incidents from './pages/Incidents'
import Personas from './pages/Personas'
import SoarPlaybooks from './pages/SoarPlaybooks'
import UserManagement from './pages/UserManagement'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
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
                  <Route path="/threat-management" element={<ThreatManagement />} />
                  <Route path="/access-governance" element={<AccessGovernance />} />
                  <Route path="/incidents" element={<Incidents />} />
                  <Route path="/personas" element={<Personas />} />
                  <Route path="/soar-playbooks" element={<SoarPlaybooks />} />
                  <Route path="/users" element={<UserManagement />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App

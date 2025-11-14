import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { agentApi, gatewayApi, Gateway, AgentStatus } from '../services/api'
import AgentStatusBadge from '../components/AgentStatusBadge'
import HealthIndicator from '../components/HealthIndicator'
import AgentConfigViewer from '../components/AgentConfigViewer'

// Mock org_id for now - in production, get from auth context
// Using the actual org_id from the database where gateways are registered
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function AgentManagement() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)

  // Poll agents list every 8 seconds
  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents', MOCK_ORG_ID],
    queryFn: () => agentApi.listAgents(MOCK_ORG_ID),
    refetchInterval: 8000,
  })

  // Filter out test/demo agents - only show real agents
  const agents = agentsData?.filter(
    (agent) => 
      !agent.name.toLowerCase().includes('test') &&
      !agent.instance_id.toLowerCase().includes('test')
  ) || []

  // Fetch detailed status for selected agent
  const { data: agentStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['agent-status', selectedAgent, MOCK_ORG_ID],
    queryFn: () => {
      if (!selectedAgent) return null
      return agentApi.getStatus(selectedAgent, MOCK_ORG_ID)
    },
    enabled: !!selectedAgent && showDetailModal,
    refetchInterval: 5000,
  })

  // Fetch config for selected agent
  const { 
    data: agentConfig, 
    isLoading: configLoading, 
    error: configError 
  } = useQuery({
    queryKey: ['agent-config', selectedAgent, MOCK_ORG_ID],
    queryFn: () => {
      if (!selectedAgent) return null
      return agentApi.getConfig(selectedAgent, MOCK_ORG_ID)
    },
    enabled: !!selectedAgent && showConfigModal,
    retry: false, // Don't retry on error to show error message immediately
  })

  const handleViewDetails = (agentId: string) => {
    setSelectedAgent(agentId)
    setShowDetailModal(true)
    setShowConfigModal(false)
  }

  const handleViewConfig = (agentId: string) => {
    setSelectedAgent(agentId)
    setShowConfigModal(true)
    setShowDetailModal(false)
  }

  const formatLastSeen = (lastSeen?: string) => {
    if (!lastSeen) return 'Never'
    const date = new Date(lastSeen)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return date.toLocaleString()
  }

  const getHealthStatus = (agent: Gateway): 'healthy' | 'warning' | 'unhealthy' | 'offline' => {
    if (!agent.last_seen) return 'unhealthy'
    const lastSeen = new Date(agent.last_seen)
    const now = new Date()
    const seconds = Math.floor((now.getTime() - lastSeen.getTime()) / 1000)
    
    if (agent.status === 'offline' || agent.status === 'inactive' || agent.status === 'error') return 'offline'
    if (seconds <= 60) return 'healthy'
    if (seconds <= 300) return 'warning'
    return 'unhealthy'
  }

  if (agentsLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">
          <div className="text-gray-500">Loading agents...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">OpAMP Agent Management</h1>
        <p className="mt-2 text-sm text-gray-600">
          Monitor and manage your OpenTelemetry Collector agents
        </p>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name / Instance ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Health
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Seen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Config Version
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {agents && agents.length > 0 ? (
                agents.map((agent) => {
                  const healthStatus = getHealthStatus(agent)
                  const version = agent.metadata?.version || agent.version || 'N/A'
                  
                  return (
                    <tr key={agent.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{agent.name}</div>
                          <div className="text-sm text-gray-500">{agent.instance_id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <AgentStatusBadge status={agent.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <AgentStatusBadge status={healthStatus} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {version}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatLastSeen(agent.last_seen)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {agent.current_config_version ?? agent.config_version ?? 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleViewDetails(agent.id)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Details
                        </button>
                        <button
                          onClick={() => handleViewConfig(agent.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Config
                        </button>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-sm text-gray-500">
                    No agents found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Agent Detail Modal */}
      {showDetailModal && selectedAgent && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Agent Details</h3>
              <button
                onClick={() => {
                  setShowDetailModal(false)
                  setSelectedAgent(null)
                }}
                className="text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {statusLoading ? (
              <div className="text-center py-8">Loading...</div>
            ) : agentStatus ? (
              <div className="space-y-6">
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Agent Information</h4>
                  <dl className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <dt className="text-gray-500">Name</dt>
                      <dd className="text-gray-900">{agentStatus.name}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Instance ID</dt>
                      <dd className="text-gray-900 font-mono text-xs">{agentStatus.instance_id}</dd>
                    </div>
                  </dl>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Health Status</h4>
                  <HealthIndicator health={agentStatus.health} />
                </div>

                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Version Information</h4>
                  <dl className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <dt className="text-gray-500">Agent Version</dt>
                      <dd className="text-gray-900">{agentStatus.version.agent_version || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">OTel Version</dt>
                      <dd className="text-gray-900">{agentStatus.version.otel_version || 'N/A'}</dd>
                    </div>
                    {agentStatus.version.capabilities && agentStatus.version.capabilities.length > 0 && (
                      <div className="col-span-2">
                        <dt className="text-gray-500">Capabilities</dt>
                        <dd className="text-gray-900">
                          <div className="flex flex-wrap gap-2 mt-1">
                            {agentStatus.version.capabilities.map((cap, idx) => (
                              <span key={idx} className="px-2 py-1 bg-gray-100 rounded text-xs">
                                {cap}
                              </span>
                            ))}
                          </div>
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>

                {agentStatus.metrics && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Metrics</h4>
                    <dl className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <dt className="text-gray-500">Logs Processed</dt>
                        <dd className="text-gray-900">{agentStatus.metrics.logs_processed?.toLocaleString() || 'N/A'}</dd>
                      </div>
                      <div>
                        <dt className="text-gray-500">Errors</dt>
                        <dd className="text-gray-900">{agentStatus.metrics.errors?.toLocaleString() || 'N/A'}</dd>
                      </div>
                      <div>
                        <dt className="text-gray-500">Latency</dt>
                        <dd className="text-gray-900">{agentStatus.metrics.latency_ms ? `${agentStatus.metrics.latency_ms.toFixed(2)}ms` : 'N/A'}</dd>
                      </div>
                    </dl>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">Failed to load agent details</div>
            )}
          </div>
        </div>
      )}

      {/* Config Viewer Modal */}
      {showConfigModal && selectedAgent && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-4/5 lg:w-3/4 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Agent Configuration</h3>
              <button
                onClick={() => {
                  setShowConfigModal(false)
                  setSelectedAgent(null)
                }}
                className="text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {configLoading ? (
              <div className="text-center py-8">Loading configuration...</div>
            ) : configError ? (
              <div className="text-center py-8">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center justify-center mb-2">
                    <svg className="h-5 w-5 text-red-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <h4 className="text-sm font-medium text-red-800">Failed to Load Configuration</h4>
                  </div>
                  <p className="text-sm text-red-700 mt-2">
                    {configError instanceof Error 
                      ? configError.message 
                      : 'Unable to retrieve agent configuration. The agent may not have an active configuration deployed.'}
                  </p>
                  <p className="text-xs text-red-600 mt-2">
                    Please ensure the agent is properly registered and has an active deployment.
                  </p>
                </div>
              </div>
            ) : agentConfig ? (
              <AgentConfigViewer config={agentConfig} />
            ) : (
              <div className="text-center py-8 text-gray-500">No active configuration found</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


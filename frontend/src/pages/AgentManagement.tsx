import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { agentApi, gatewayApi, Gateway, AgentStatus, opampConfigApi, AgentConfigHistoryEntry } from '../services/api'
import AgentStatusBadge from '../components/AgentStatusBadge'
import HealthIndicator from '../components/HealthIndicator'
import AgentConfigViewer from '../components/AgentConfigViewer'
import { OpAMPStatusBadge } from '../components/OpAMPStatusBadge'
import { RemoteConfigStatusBadge } from '../components/RemoteConfigStatusBadge'
import { CapabilitiesDisplay } from '../components/CapabilitiesDisplay'
import AgentTagManager from '../components/AgentTagManager'
import SupervisorStatus from '../components/SupervisorStatus'
import SupervisorConfigEditor from '../components/SupervisorConfigEditor'
import { supervisorApi } from '../services/api'

// Mock org_id for now - in production, get from auth context
// Using the actual org_id from the database where gateways are registered
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function AgentManagement() {
  const navigate = useNavigate()
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [showTagManager, setShowTagManager] = useState(false)
  const [tagManagerAgentId, setTagManagerAgentId] = useState<string | null>(null)
  const [showSupervisorLogs, setShowSupervisorLogs] = useState(false)
  const [showSupervisorConfig, setShowSupervisorConfig] = useState(false)
  const queryClient = useQueryClient()

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

  // Fetch config history for selected agent
  const { 
    data: configHistory, 
    isLoading: historyLoading 
  } = useQuery({
    queryKey: ['agent-config-history', selectedAgent, MOCK_ORG_ID],
    queryFn: async () => {
      if (!selectedAgent) return null
      try {
        const response = await fetch(`/api/v1/gateways/${selectedAgent}/config-history?org_id=${MOCK_ORG_ID}`)
        if (response.ok) {
          return await response.json()
        }
        return []
      } catch {
        return []
      }
    },
    enabled: !!selectedAgent && showDetailModal,
  })

  const handleViewDetails = (instanceId: string) => {
    // Navigate to dedicated agent details page
    navigate(`/agents/${instanceId}`)
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
                  OpAMP Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Config Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Transport
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
                        {agent.last_config_version ?? agent.current_config_version ?? agent.config_version ?? 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {agent.opamp_connection_status ? (
                          <OpAMPStatusBadge status={agent.opamp_connection_status} />
                        ) : (
                          <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {agent.last_config_status || agent.opamp_remote_config_status ? (
                          <RemoteConfigStatusBadge status={(agent.last_config_status || agent.opamp_remote_config_status) as any} />
                        ) : (
                          <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {agent.opamp_transport_type ? (
                          <span className="capitalize">{agent.opamp_transport_type}</span>
                        ) : (
                          <span className="text-xs text-gray-400">N/A</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          agent.management_mode === 'supervisor'
                            ? 'bg-purple-100 text-purple-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {agent.management_mode === 'supervisor' ? 'Supervisor' : 'Extension'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleViewDetails(agent.instance_id)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Details
                        </button>
                        <button
                          onClick={() => handleViewConfig(agent.id)}
                          className="text-blue-600 hover:text-blue-900 mr-4"
                        >
                          Config
                        </button>
                        {agent.management_mode === 'supervisor' && (
                          <>
                            <button
                              onClick={() => {
                                setSelectedAgent(agent.instance_id)
                                setShowSupervisorLogs(true)
                              }}
                              className="text-purple-600 hover:text-purple-900 mr-4"
                            >
                              Logs
                            </button>
                            <button
                              onClick={() => {
                                setSelectedAgent(agent.instance_id)
                                setShowSupervisorConfig(true)
                              }}
                              className="text-indigo-600 hover:text-indigo-900"
                            >
                              Push Config
                            </button>
                          </>
                        )}
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={10} className="px-6 py-4 text-center text-sm text-gray-500">
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
                      <dd className="text-gray-900 font-mono text-xs">{selectedAgent}</dd>
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

                {/* OpAMP Connection Information */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">OpAMP Connection Information</h4>
                  <dl className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <dt className="text-gray-500">Connection Status</dt>
                      <dd className="text-gray-900 mt-1">
                        <OpAMPStatusBadge status={agentStatus.opamp_connection_status || null} />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Transport Type</dt>
                      <dd className="text-gray-900">{agentStatus.opamp_transport_type || 'N/A'}</dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Last Sequence Number</dt>
                      <dd className="text-gray-900 font-mono text-xs">
                        {agentStatus.opamp_last_sequence_num !== null && agentStatus.opamp_last_sequence_num !== undefined
                          ? agentStatus.opamp_last_sequence_num
                          : 'N/A'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Registration Status</dt>
                      <dd className="text-gray-900">
                        {agentStatus.opamp_registration_failed ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="text-red-600">Failed</span>
                            {agentStatus.opamp_registration_failure_reason && (
                              <span className="text-xs text-gray-500">({agentStatus.opamp_registration_failure_reason})</span>
                            )}
                          </span>
                        ) : (
                          <span className="text-green-600">Registered</span>
                        )}
                      </dd>
                    </div>
                  </dl>
                </div>

                {/* OpAMP Capabilities */}
                {(agentStatus.opamp_agent_capabilities !== null && agentStatus.opamp_agent_capabilities !== undefined) ||
                (agentStatus.opamp_server_capabilities !== null && agentStatus.opamp_server_capabilities !== undefined) ? (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">OpAMP Capabilities</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {agentStatus.opamp_agent_capabilities !== null && agentStatus.opamp_agent_capabilities !== undefined && (
                        <CapabilitiesDisplay
                          bitField={agentStatus.opamp_agent_capabilities}
                          decoded={agentStatus.opamp_agent_capabilities_decoded || undefined}
                          label="Agent Capabilities"
                        />
                      )}
                      {agentStatus.opamp_server_capabilities !== null && agentStatus.opamp_server_capabilities !== undefined && (
                        <CapabilitiesDisplay
                          bitField={agentStatus.opamp_server_capabilities}
                          decoded={agentStatus.opamp_server_capabilities_decoded || undefined}
                          label="Server Capabilities"
                        />
                      )}
                    </div>
                  </div>
                ) : null}

                {/* Supervisor Status - Only show if supervisor-managed */}
                {agentStatus && agentStatus.management_mode === 'supervisor' && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Supervisor Status</h4>
                    <SupervisorStatus instanceId={selectedAgent} />
                  </div>
                )}

                {/* Configuration Status */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Configuration Status</h4>
                  <dl className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <dt className="text-gray-500">Remote Config Status</dt>
                      <dd className="text-gray-900 mt-1">
                        <RemoteConfigStatusBadge status={agentStatus.opamp_remote_config_status || null} />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Effective Config Hash</dt>
                      <dd className="text-gray-900 font-mono text-xs break-all">
                        {agentStatus.opamp_effective_config_hash || 'N/A'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Remote Config Hash</dt>
                      <dd className="text-gray-900 font-mono text-xs break-all">
                        {agentStatus.opamp_remote_config_hash || 'N/A'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Last Config Version</dt>
                      <dd className="text-gray-900">
                        {agentStatus.opamp_last_sequence_num !== null ? agentStatus.opamp_last_sequence_num : 'N/A'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-gray-500">Config Sync</dt>
                      <dd className="text-gray-900">
                        {agentStatus.opamp_effective_config_hash &&
                        agentStatus.opamp_remote_config_hash &&
                        agentStatus.opamp_effective_config_hash === agentStatus.opamp_remote_config_hash ? (
                          <span className="text-green-600">✓ In Sync</span>
                        ) : (
                          <span className="text-yellow-600">⚠ Out of Sync</span>
                        )}
                      </dd>
                    </div>
                  </dl>
                </div>

                {/* Configuration History */}
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Configuration History</h4>
                  {historyLoading ? (
                    <div className="text-sm text-gray-500">Loading history...</div>
                  ) : configHistory && configHistory.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200 text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Version</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Deployment</th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Updated</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {configHistory.slice(0, 10).map((entry: AgentConfigHistoryEntry) => (
                            <tr key={entry.audit_id}>
                              <td className="px-3 py-2 whitespace-nowrap text-gray-900">{entry.config_version}</td>
                              <td className="px-3 py-2 whitespace-nowrap">
                                <RemoteConfigStatusBadge status={entry.status as any} />
                              </td>
                              <td className="px-3 py-2 text-gray-500 text-xs">
                                {entry.deployment_name || 'N/A'}
                              </td>
                              <td className="px-3 py-2 text-gray-500 text-xs">
                                {entry.status_reported_at ? new Date(entry.status_reported_at).toLocaleString() : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="text-sm text-gray-500">No configuration history available</div>
                  )}
                </div>

                {/* Tag Management */}
                <div className="border-t pt-4 mt-4">
                  <div className="flex justify-between items-center">
                    <h4 className="text-sm font-medium text-gray-900">Tags</h4>
                    <button
                      onClick={() => {
                        setTagManagerAgentId(selectedAgent)
                        setShowTagManager(true)
                      }}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Manage Tags
                    </button>
                  </div>
                  {agentStatus && (agentStatus as any).tags && (agentStatus as any).tags.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {(agentStatus as any).tags.map((tag: string) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 mt-2">No tags assigned</p>
                  )}
                </div>

                {/* Push Config Button */}
                <div className="border-t pt-4 mt-4">
                  <button
                    onClick={() => {
                      setShowDetailModal(false)
                      // Navigate to create deployment with pre-filled agent
                      window.location.href = `/opamp-config/create?gateway_id=${selectedAgent}`
                    }}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Push Config to This Agent
                  </button>
                </div>

                {/* Registration Restart Button */}
                {agentStatus.opamp_registration_failed && (
                  <div className="border-t pt-4 mt-4">
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <div className="flex items-start">
                        <div className="flex-shrink-0">
                          <svg className="h-5 w-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </div>
                        <div className="ml-3 flex-1">
                          <h5 className="text-sm font-medium text-yellow-800">Registration Failed</h5>
                          <p className="mt-1 text-sm text-yellow-700">
                            {agentStatus.opamp_registration_failure_reason || 'Registration failed. Click below to retry.'}
                          </p>
                          <div className="mt-3">
                            <button
                              onClick={() => {
                                // TODO: Implement registration restart
                                alert('Registration restart functionality will be implemented. Please use the registration token to restart registration.')
                              }}
                              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-yellow-800 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500"
                            >
                              Restart Registration
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
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

      {/* Tag Manager Modal */}
      {showTagManager && tagManagerAgentId && (
        <AgentTagManager
          gatewayId={tagManagerAgentId}
          orgId={MOCK_ORG_ID}
          onClose={() => {
            setShowTagManager(false)
            setTagManagerAgentId(null)
          }}
        />
      )}

      {/* Supervisor Logs Modal */}
      {showSupervisorLogs && selectedAgent && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Supervisor Logs - {selectedAgent}</h3>
              <button
                onClick={() => {
                  setShowSupervisorLogs(false)
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
            <SupervisorLogsViewer instanceId={selectedAgent} />
          </div>
        </div>
      )}

      {/* Supervisor Config Editor Modal */}
      {showSupervisorConfig && selectedAgent && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Push Configuration - {selectedAgent}</h3>
              <button
                onClick={() => {
                  setShowSupervisorConfig(false)
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
            <SupervisorConfigEditor
              instanceId={selectedAgent}
              onSuccess={() => {
                setShowSupervisorConfig(false)
                setSelectedAgent(null)
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}

// Supervisor Logs Viewer Component
function SupervisorLogsViewer({ instanceId }: { instanceId: string }) {
  const { data: logsData, isLoading } = useQuery({
    queryKey: ['supervisor-logs', instanceId],
    queryFn: () => supervisorApi.getLogs(instanceId, MOCK_ORG_ID, 200),
    refetchInterval: 5000,
  })

  if (isLoading) {
    return <div className="text-center py-8">Loading logs...</div>
  }

  return (
    <div className="bg-gray-900 text-green-400 font-mono text-xs p-4 rounded-md max-h-96 overflow-auto">
      <pre className="whitespace-pre-wrap">{logsData?.logs || 'No logs available'}</pre>
    </div>
  )
}


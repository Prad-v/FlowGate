import React from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { supervisorApi } from '../services/api'
import { OpAMPStatusBadge } from '../components/OpAMPStatusBadge'
import { RemoteConfigStatusBadge } from '../components/RemoteConfigStatusBadge'
import { CapabilitiesDisplay } from '../components/CapabilitiesDisplay'
import AgentConfigViewer from '../components/AgentConfigViewer'
import SupervisorStatus from '../components/SupervisorStatus'
import ConfigDiffViewer from '../components/ConfigDiffViewer'

// Mock org_id for now - in production, get from auth context
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function AgentDetails() {
  const { instanceId } = useParams<{ instanceId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // All hooks must be called before any conditional returns
  const { data: agentDetails, isLoading, error } = useQuery({
    queryKey: ['agent-details', instanceId, MOCK_ORG_ID],
    queryFn: () => {
      if (!instanceId) throw new Error('Instance ID is required')
      return supervisorApi.getAgentDetails(instanceId, MOCK_ORG_ID)
    },
    enabled: !!instanceId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  // State for tracking config request
  const [trackingId, setTrackingId] = React.useState<string | null>(null)
  const [configRequestStatus, setConfigRequestStatus] = React.useState<any>(null)

  // Mutation to request effective config from agent
  const requestEffectiveConfigMutation = useMutation({
    mutationFn: () => {
      if (!instanceId) throw new Error('Instance ID is required')
      return supervisorApi.requestEffectiveConfig(instanceId, MOCK_ORG_ID)
    },
    onSuccess: (data) => {
      // Store tracking ID
      if (data.tracking_id) {
        setTrackingId(data.tracking_id)
        // Start polling for status
        pollConfigRequestStatus(data.tracking_id)
      }
      // Refetch agent details after a short delay to get the effective config
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['agent-details', instanceId, MOCK_ORG_ID] })
      }, 2000)
    },
  })

  // Poll for config request status
  const pollConfigRequestStatus = React.useCallback((trackId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await supervisorApi.getConfigRequestStatus(instanceId!, trackId, MOCK_ORG_ID)
        setConfigRequestStatus(status)
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
          // Refetch agent details to get the new config
          queryClient.invalidateQueries({ queryKey: ['agent-details', instanceId, MOCK_ORG_ID] })
        }
      } catch (error) {
        console.error('Error polling config request status:', error)
        clearInterval(pollInterval)
      }
    }, 2000) // Poll every 2 seconds

    // Cleanup on unmount
    return () => clearInterval(pollInterval)
  }, [instanceId, queryClient])

  // State for config comparison
  const [showDiffViewer, setShowDiffViewer] = React.useState(false)
  const [diffData, setDiffData] = React.useState<any>(null)
  const compareConfigMutation = useMutation({
    mutationFn: () => {
      if (!instanceId) throw new Error('Instance ID is required')
      return supervisorApi.compareConfig(instanceId, null, null, MOCK_ORG_ID)
    },
    onSuccess: (data) => {
      setDiffData(data)
      setShowDiffViewer(true)
    },
  })

  // Helper function
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

  const handleRequestEffectiveConfig = () => {
    requestEffectiveConfigMutation.mutate()
  }

  // Extract config data (safe to do after hooks)
  const effectiveConfig = agentDetails?.effective_config
  const currentConfig = agentDetails?.current_config

  // Conditional returns after all hooks
  if (isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">
          <div className="text-gray-500">Loading agent details...</div>
        </div>
      </div>
    )
  }

  if (error || !agentDetails) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-sm font-medium text-red-800">Failed to Load Agent Details</h3>
          </div>
          <p className="mt-2 text-sm text-red-700">
            {error instanceof Error ? error.message : 'Unable to retrieve agent details. The agent may not exist or you may not have permission to view it.'}
          </p>
          <button
            onClick={() => navigate('/agents')}
            className="mt-4 text-sm text-red-600 hover:text-red-800 underline"
          >
            Back to Agents
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/agents')}
          className="text-sm text-gray-600 hover:text-gray-900 mb-4 flex items-center"
        >
          <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Agents
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{agentDetails.name || 'Agent Details'}</h1>
            <p className="mt-2 text-sm text-gray-600">
              Instance ID: <span className="font-mono">{agentDetails.instance_id}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
              agentDetails.management_mode === 'supervisor'
                ? 'bg-purple-100 text-purple-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {agentDetails.management_mode === 'supervisor' ? 'Supervisor' : 'Extension'}
            </span>
            {agentDetails.opamp_connection_status && (
              <OpAMPStatusBadge status={agentDetails.opamp_connection_status} />
            )}
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Agent Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Agent Information</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Name</dt>
              <dd className="mt-1 text-sm text-gray-900">{agentDetails.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Instance ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{agentDetails.instance_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Gateway ID</dt>
              <dd className="mt-1 text-sm text-gray-900 font-mono">{agentDetails.gateway_id}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Management Mode</dt>
              <dd className="mt-1">
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                  agentDetails.management_mode === 'supervisor'
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {agentDetails.management_mode === 'supervisor' ? 'Supervisor' : 'Extension'}
                </span>
              </dd>
            </div>
            {agentDetails.hostname && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Hostname</dt>
                <dd className="mt-1 text-sm text-gray-900">{agentDetails.hostname}</dd>
              </div>
            )}
            {agentDetails.ip_address && (
              <div>
                <dt className="text-sm font-medium text-gray-500">IP Address</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{agentDetails.ip_address}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-500">Last Seen</dt>
              <dd className="mt-1 text-sm text-gray-900">{formatLastSeen(agentDetails.last_seen)}</dd>
            </div>
          </dl>
        </div>

        {/* Version Information */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Version Information</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agentDetails.agent_version && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Agent Version</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {typeof agentDetails.agent_version === 'string' 
                    ? agentDetails.agent_version 
                    : agentDetails.agent_version?.version || 'N/A'}
                </dd>
              </div>
            )}
            {agentDetails.agent_name && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Agent Name</dt>
                <dd className="mt-1 text-sm text-gray-900">{agentDetails.agent_name}</dd>
              </div>
            )}
            {agentDetails.identifying_attributes && Object.keys(agentDetails.identifying_attributes).length > 0 && (
              <div className="col-span-2">
                <dt className="text-sm font-medium text-gray-500 mb-2">Identifying Attributes</dt>
                <dd className="mt-1">
                  <div className="bg-gray-50 rounded-md p-3">
                    <dl className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {Object.entries(agentDetails.identifying_attributes).map(([key, value]) => (
                        <div key={key}>
                          <dt className="text-xs font-medium text-gray-600">{key}</dt>
                          <dd className="text-xs text-gray-900 font-mono">{String(value)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                </dd>
              </div>
            )}
          </dl>
        </div>

        {/* Health & Metrics */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Health & Metrics</h2>
          <div className="space-y-4">
            {agentDetails.health && Object.keys(agentDetails.health).length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Health Status</h3>
                <div className="bg-gray-50 rounded-md p-3">
                  <dl className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {agentDetails.health.healthy !== undefined && (
                      <div>
                        <dt className="text-xs font-medium text-gray-600">Healthy</dt>
                        <dd className="text-xs text-gray-900">
                          <span className={`px-2 py-1 rounded ${
                            agentDetails.health.healthy ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {agentDetails.health.healthy ? 'Yes' : 'No'}
                          </span>
                        </dd>
                      </div>
                    )}
                    {agentDetails.health.start_time_unix_nano && (
                      <div>
                        <dt className="text-xs font-medium text-gray-600">Start Time</dt>
                        <dd className="text-xs text-gray-900">
                          {new Date(Number(agentDetails.health.start_time_unix_nano) / 1000000).toLocaleString()}
                        </dd>
                      </div>
                    )}
                    {agentDetails.health.last_error && (
                      <div className="col-span-2">
                        <dt className="text-xs font-medium text-gray-600">Last Error</dt>
                        <dd className="text-xs text-red-600">{agentDetails.health.last_error}</dd>
                      </div>
                    )}
                  </dl>
                </div>
              </div>
            )}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Connection Metrics</h3>
              <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Last Seen</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {agentDetails.connection_metrics?.last_seen 
                      ? formatLastSeen(agentDetails.connection_metrics.last_seen)
                      : 'Never'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Sequence Number</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono">
                    {agentDetails.connection_metrics?.sequence_num ?? agentDetails.opamp_last_sequence_num ?? 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Transport Type</dt>
                  <dd className="mt-1 text-sm text-gray-900 capitalize">
                    {agentDetails.connection_metrics?.transport_type ?? agentDetails.opamp_transport_type ?? 'N/A'}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* OpAMP Capabilities */}
        {(agentDetails.opamp_agent_capabilities !== null && agentDetails.opamp_agent_capabilities !== undefined) ||
        (agentDetails.opamp_server_capabilities !== null && agentDetails.opamp_server_capabilities !== undefined) ? (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">OpAMP Capabilities</h2>
            <div className="grid grid-cols-1 gap-6">
              {agentDetails.opamp_agent_capabilities !== null && agentDetails.opamp_agent_capabilities !== undefined && (
                <CapabilitiesDisplay
                  bitField={agentDetails.opamp_agent_capabilities}
                  decoded={agentDetails.opamp_agent_capabilities_decoded || undefined}
                  label="Agent Capabilities"
                  detailed={true}
                  agentData={{
                    instance_id: agentDetails.instance_id,
                    agent_version: agentDetails.agent_version,
                    health: agentDetails.health,
                    opamp_effective_config_hash: agentDetails.opamp_effective_config_hash,
                    opamp_remote_config_status: agentDetails.opamp_remote_config_status,
                    opamp_remote_config_hash: agentDetails.opamp_remote_config_hash,
                    opamp_last_sequence_num: agentDetails.opamp_last_sequence_num,
                    identifying_attributes: agentDetails.identifying_attributes,
                  }}
                />
              )}
              {agentDetails.opamp_server_capabilities !== null && agentDetails.opamp_server_capabilities !== undefined && (
                <CapabilitiesDisplay
                  bitField={agentDetails.opamp_server_capabilities}
                  decoded={agentDetails.opamp_server_capabilities_decoded || undefined}
                  label="Server Capabilities"
                  detailed={true}
                />
              )}
            </div>
          </div>
        ) : null}

        {/* OpAMP Connection */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">OpAMP Connection</h2>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500">Connection Status</dt>
              <dd className="mt-1">
                {agentDetails.opamp_connection_status ? (
                  <OpAMPStatusBadge status={agentDetails.opamp_connection_status} />
                ) : (
                  <span className="text-sm text-gray-400">N/A</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Remote Config Status</dt>
              <dd className="mt-1">
                {agentDetails.opamp_remote_config_status ? (
                  <RemoteConfigStatusBadge status={agentDetails.opamp_remote_config_status as any} />
                ) : (
                  <span className="text-sm text-gray-400">N/A</span>
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Transport Type</dt>
              <dd className="mt-1 text-sm text-gray-900 capitalize">
                {agentDetails.opamp_transport_type || 'N/A'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Config Sync</dt>
              <dd className="mt-1">
                {agentDetails.opamp_effective_config_hash &&
                agentDetails.opamp_remote_config_hash &&
                agentDetails.opamp_effective_config_hash === agentDetails.opamp_remote_config_hash ? (
                  <span className="text-sm text-green-600">✓ In Sync</span>
                ) : (
                  <span className="text-sm text-yellow-600">⚠ Out of Sync</span>
                )}
              </dd>
            </div>
            {agentDetails.opamp_registration_failed && (
              <div className="col-span-2">
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <svg className="h-5 w-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <h4 className="text-sm font-medium text-yellow-800">Registration Failed</h4>
                      <p className="mt-1 text-sm text-yellow-700">
                        {agentDetails.opamp_registration_failure_reason || 'Registration failed. Please check the agent configuration.'}
                      </p>
                      {agentDetails.opamp_registration_failed_at && (
                        <p className="mt-1 text-xs text-yellow-600">
                          Failed at: {new Date(agentDetails.opamp_registration_failed_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </dl>
        </div>

        {/* Supervisor Status */}
        {agentDetails.management_mode === 'supervisor' && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Supervisor Status</h2>
            <SupervisorStatus instanceId={agentDetails.instance_id} />
          </div>
        )}

        {/* Effective Configuration */}
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-gray-900">Effective Configuration</h2>
            <div className="flex items-center gap-2">
              {trackingId && (
                <div className="text-sm text-gray-600">
                  <span className="font-mono text-xs">Tracking ID: </span>
                  <button
                    onClick={() => {
                      const url = `/agents/${instanceId}/config-requests/${trackingId}`
                      navigator.clipboard.writeText(url)
                      alert('Tracking ID copied to clipboard')
                    }}
                    className="font-mono text-xs text-blue-600 hover:text-blue-800 underline"
                    title="Click to copy tracking ID"
                  >
                    {trackingId.substring(0, 8)}...
                  </button>
                  {configRequestStatus && (
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      configRequestStatus.status === 'completed' ? 'bg-green-100 text-green-800' :
                      configRequestStatus.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {configRequestStatus.status}
                    </span>
                  )}
                </div>
              )}
              {(!effectiveConfig?.config_yaml && agentDetails.opamp_agent_capabilities && 
                (agentDetails.opamp_agent_capabilities & 0x04)) && ( // ReportsEffectiveConfig capability
                <button
                  onClick={handleRequestEffectiveConfig}
                  disabled={requestEffectiveConfigMutation.isPending}
                  className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {requestEffectiveConfigMutation.isPending ? 'Requesting...' : 'Request Config'}
                </button>
              )}
            </div>
          </div>
          {effectiveConfig ? (
            effectiveConfig.config_yaml ? (
              <div>
                <div className="mb-4 flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    {effectiveConfig.deployment_name && (
                      <span>Deployment: {effectiveConfig.deployment_name}</span>
                    )}
                    {effectiveConfig.config_version && (
                      <span className="ml-4">Version: {effectiveConfig.config_version}</span>
                    )}
                    {effectiveConfig.source && (
                      <span className="ml-4 text-gray-500">Source: {effectiveConfig.source}</span>
                    )}
                  </div>
                  <button
                    onClick={() => compareConfigMutation.mutate()}
                    disabled={compareConfigMutation.isPending}
                    className="px-3 py-1.5 text-sm font-medium text-blue-700 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {compareConfigMutation.isPending ? 'Comparing...' : 'Compare with Standard'}
                  </button>
                </div>
                {showDiffViewer && diffData ? (
                  <div className="mb-4">
                    <button
                      onClick={() => setShowDiffViewer(false)}
                      className="mb-2 text-sm text-gray-600 hover:text-gray-800"
                    >
                      ← Hide Comparison
                    </button>
                    <ConfigDiffViewer
                      agentConfig={diffData.agent_config}
                      standardConfig={diffData.standard_config}
                      diff={diffData.diff}
                      diffStats={diffData.diff_stats}
                    />
                  </div>
                ) : (
                  <AgentConfigViewer
                    config={{
                      config_yaml: effectiveConfig.config_yaml,
                      config_version: effectiveConfig.config_version,
                      last_updated: undefined,
                    }}
                  />
                )}
              </div>
            ) : (
              <div className="text-sm text-gray-500">
                <p>Effective config hash: <span className="font-mono text-xs">{effectiveConfig.hash || 'N/A'}</span></p>
                <p className="mt-2">Config content not available. The deployment matching this hash may have been deleted.</p>
                {trackingId && (
                  <div className="mt-2">
                    <p className="text-blue-600">
                      Request sent. Tracking ID: <span className="font-mono text-xs">{trackingId}</span>
                    </p>
                    {configRequestStatus?.status === 'pending' && (
                      <p className="mt-1 text-sm text-gray-600">Waiting for agent to report effective config...</p>
                    )}
                    {configRequestStatus?.status === 'completed' && (
                      <p className="mt-1 text-sm text-green-600">✓ Config received successfully!</p>
                    )}
                    {configRequestStatus?.status === 'failed' && (
                      <p className="mt-1 text-sm text-red-600">✗ Request failed: {configRequestStatus.error_message}</p>
                    )}
                  </div>
                )}
              </div>
            )
          ) : (
            <div className="text-sm text-gray-500">
              <p>No effective configuration reported by agent yet.</p>
              {agentDetails.opamp_agent_capabilities && (agentDetails.opamp_agent_capabilities & 0x04) && (
                <p className="mt-2">Click "Request Config" to ask the agent to report its effective configuration.</p>
              )}
            </div>
          )}
        </div>

        {/* Current Configuration (if different from effective) */}
        {currentConfig && currentConfig.config_yaml && 
         (!effectiveConfig?.config_yaml || currentConfig.config_yaml !== effectiveConfig.config_yaml) && (
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Current/Pending Configuration</h2>
            <div className="mb-4 text-sm text-gray-600">
              {currentConfig.deployment_id && <span>Deployment ID: <span className="font-mono text-xs">{currentConfig.deployment_id}</span></span>}
              {currentConfig.config_version && <span className="ml-4">Version: {currentConfig.config_version}</span>}
            </div>
            <AgentConfigViewer
              config={{
                config_yaml: currentConfig.config_yaml,
                config_version: currentConfig.config_version,
                last_updated: undefined,
              }}
            />
          </div>
        )}
      </div>
    </div>
  )
}


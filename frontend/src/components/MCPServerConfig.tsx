import { useState, useEffect, useCallback } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  MCPServerCreate,
  MCPServerUpdate,
  MCPServerResponse,
  mcpServerApi,
  MCPServerTypeInfo,
  MCPConnectionTestResponse,
  MCPResourceDiscoveryResponse,
} from '../services/api'

interface MCPServerConfigProps {
  initialConfig?: MCPServerResponse | null
  onSave: () => void
  onCancel?: () => void
}

export default function MCPServerConfig({ initialConfig, onSave, onCancel }: MCPServerConfigProps) {
  const [serverType, setServerType] = useState<'grafana' | 'aws' | 'gcp' | 'custom'>(
    (initialConfig?.server_type as any) || 'grafana'
  )
  const [serverName, setServerName] = useState(initialConfig?.server_name || '')
  const [endpointUrl, setEndpointUrl] = useState(initialConfig?.endpoint_url || '')
  const [authType, setAuthType] = useState<'oauth' | 'custom_header' | 'no_auth'>(
    (initialConfig?.auth_type as any) || 'no_auth'
  )
  const [authConfig, setAuthConfig] = useState<Record<string, any>>(initialConfig?.auth_config || {})
  const [scope, setScope] = useState<'personal' | 'tenant'>(
    (initialConfig?.scope as any) || 'personal'
  )
  const [metadata, setMetadata] = useState<Record<string, any>>(initialConfig?.metadata || {})
  const [isEnabled, setIsEnabled] = useState(initialConfig?.is_enabled || false)
  
  const [testResult, setTestResult] = useState<MCPConnectionTestResponse | null>(null)
  const [discoveryResult, setDiscoveryResult] = useState<MCPResourceDiscoveryResponse | null>(null)
  const [showResources, setShowResources] = useState(false)

  // Fetch server types for validation
  const { data: serverTypes } = useQuery({
    queryKey: ['mcp-server-types'],
    queryFn: () => mcpServerApi.getServerTypes(),
  })

  const currentServerTypeInfo = serverTypes?.find((st) => st.server_type === serverType)

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (data: MCPServerCreate | MCPServerUpdate) => {
      if (initialConfig) {
        return mcpServerApi.updateServer(initialConfig.id, data as MCPServerUpdate)
      } else {
        return mcpServerApi.createServer(data as MCPServerCreate)
      }
    },
    onSuccess: () => {
      onSave()
    },
  })

  // Test connection mutation
  const testConnectionMutation = useMutation({
    mutationFn: async () => {
      if (!initialConfig) {
        throw new Error('Please save the server first before testing')
      }
      return mcpServerApi.testConnection(initialConfig.id)
    },
    onSuccess: (data) => {
      setTestResult(data)
      if (data.discovered_resources) {
        setDiscoveryResult({
          success: true,
          resources: data.discovered_resources,
          message: 'Resources discovered during connection test',
        })
      }
    },
  })

  // Discover resources mutation
  const discoverResourcesMutation = useMutation({
    mutationFn: async () => {
      if (!initialConfig) {
        throw new Error('Please save the server first before discovering resources')
      }
      return mcpServerApi.discoverResources(initialConfig.id)
    },
    onSuccess: (data) => {
      setDiscoveryResult(data)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const serverData: MCPServerCreate | MCPServerUpdate = {
      server_type: serverType,
      server_name: serverName,
      endpoint_url: endpointUrl || undefined,
      auth_type: authType,
      auth_config: Object.keys(authConfig).length > 0 ? authConfig : undefined,
      scope,
      metadata: Object.keys(metadata).length > 0 ? metadata : undefined,
    }

    if (!initialConfig) {
      ;(serverData as MCPServerCreate).server_type = serverType
    }

    saveMutation.mutate(serverData)
  }

  const updateAuthConfig = (key: string, value: any) => {
    setAuthConfig((prev) => ({ ...prev, [key]: value }))
  }

  const updateMetadata = (key: string, value: any) => {
    setMetadata((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-5 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">
          {initialConfig ? 'Edit MCP Server' : 'Add New MCP Server'}
        </h2>
      </div>

      <form onSubmit={handleSubmit} className="px-6 py-5 space-y-6">
        {/* Server Type */}
        <div>
          <label htmlFor="server_type" className="block text-sm font-medium text-gray-700 mb-2">
            Server Type <span className="text-red-500">*</span>
          </label>
          <select
            id="server_type"
            value={serverType}
            onChange={(e) => setServerType(e.target.value as any)}
            disabled={!!initialConfig}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
            required
          >
            <option value="grafana">Grafana</option>
            <option value="aws">Amazon Web Services</option>
            <option value="gcp">Google Cloud Platform</option>
            <option value="custom">Custom MCP Server</option>
          </select>
          {currentServerTypeInfo && (
            <p className="mt-1 text-sm text-gray-500">{currentServerTypeInfo.description}</p>
          )}
        </div>

        {/* Server Name */}
        <div>
          <label htmlFor="server_name" className="block text-sm font-medium text-gray-700 mb-2">
            Server Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="server_name"
            value={serverName}
            onChange={(e) => setServerName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>

        {/* Endpoint URL (for Grafana and Custom) */}
        {(serverType === 'grafana' || serverType === 'custom') && (
          <div>
            <label htmlFor="endpoint_url" className="block text-sm font-medium text-gray-700 mb-2">
              Endpoint URL <span className="text-red-500">*</span>
            </label>
            <input
              type="url"
              id="endpoint_url"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        )}

        {/* AWS Metadata */}
        {serverType === 'aws' && (
          <div>
            <label htmlFor="aws_region" className="block text-sm font-medium text-gray-700 mb-2">
              AWS Region <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="aws_region"
              value={metadata.region || ''}
              onChange={(e) => updateMetadata('region', e.target.value)}
              placeholder="us-east-1"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        )}

        {/* GCP Metadata */}
        {serverType === 'gcp' && (
          <div>
            <label htmlFor="gcp_project_id" className="block text-sm font-medium text-gray-700 mb-2">
              GCP Project ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="gcp_project_id"
              value={metadata.project_id || ''}
              onChange={(e) => updateMetadata('project_id', e.target.value)}
              placeholder="my-gcp-project"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
        )}

        {/* Auth Type */}
        <div>
          <label htmlFor="auth_type" className="block text-sm font-medium text-gray-700 mb-2">
            Authentication Type
          </label>
          <select
            id="auth_type"
            value={authType}
            onChange={(e) => setAuthType(e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="no_auth">No Authentication</option>
            <option value="custom_header">Custom Header (Bearer Token)</option>
            <option value="oauth">OAuth</option>
          </select>
        </div>

        {/* Auth Config */}
        {authType !== 'no_auth' && (
          <div className="space-y-4">
            <label className="block text-sm font-medium text-gray-700">Authentication Configuration</label>
            
            {authType === 'custom_header' && (
              <>
                <div>
                  <label htmlFor="auth_token" className="block text-sm font-medium text-gray-700 mb-2">
                    {serverType === 'grafana' ? 'Grafana API Token' : 'API Token / Key'}
                  </label>
                  <input
                    type="password"
                    id="auth_token"
                    value={authConfig.token || authConfig.api_key || ''}
                    onChange={(e) => updateAuthConfig(serverType === 'grafana' ? 'token' : 'api_key', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter your API token"
                  />
                </div>
              </>
            )}

            {serverType === 'aws' && (
              <>
                <div>
                  <label htmlFor="aws_access_key" className="block text-sm font-medium text-gray-700 mb-2">
                    AWS Access Key ID <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="aws_access_key"
                    value={authConfig.access_key_id || ''}
                    onChange={(e) => updateAuthConfig('access_key_id', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="aws_secret_key" className="block text-sm font-medium text-gray-700 mb-2">
                    AWS Secret Access Key <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="password"
                    id="aws_secret_key"
                    value={authConfig.secret_access_key || ''}
                    onChange={(e) => updateAuthConfig('secret_access_key', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="aws_session_token" className="block text-sm font-medium text-gray-700 mb-2">
                    AWS Session Token (Optional)
                  </label>
                  <input
                    type="text"
                    id="aws_session_token"
                    value={authConfig.session_token || ''}
                    onChange={(e) => updateAuthConfig('session_token', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}

            {serverType === 'gcp' && (
              <div>
                <label htmlFor="gcp_service_account" className="block text-sm font-medium text-gray-700 mb-2">
                  GCP Service Account Key (JSON) <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="gcp_service_account"
                  value={
                    typeof authConfig.service_account_key === 'string'
                      ? authConfig.service_account_key
                      : JSON.stringify(authConfig.service_account_key || {}, null, 2)
                  }
                  onChange={(e) => {
                    try {
                      const parsed = JSON.parse(e.target.value)
                      updateAuthConfig('service_account_key', parsed)
                    } catch {
                      updateAuthConfig('service_account_key', e.target.value)
                    }
                  }}
                  rows={10}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  placeholder='{"type": "service_account", "project_id": "...", ...}'
                  required
                />
                <p className="mt-1 text-sm text-gray-500">
                  Paste your GCP service account JSON key here
                </p>
              </div>
            )}
          </div>
        )}

        {/* Scope */}
        <div>
          <label htmlFor="scope" className="block text-sm font-medium text-gray-700 mb-2">
            Scope
          </label>
          <select
            id="scope"
            value={scope}
            onChange={(e) => setScope(e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="personal">Personal</option>
            <option value="tenant">Tenant (Shared)</option>
          </select>
        </div>

        {/* Enable/Disable (only for existing servers) */}
        {initialConfig && (
          <div className="flex items-center">
            <input
              type="checkbox"
              id="is_enabled"
              checked={isEnabled}
              onChange={(e) => setIsEnabled(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="is_enabled" className="ml-2 block text-sm text-gray-900">
              Enable this server
            </label>
          </div>
        )}

        {/* Test Connection & Discover Resources (for existing servers) */}
        {initialConfig && (
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={() => testConnectionMutation.mutate()}
              disabled={testConnectionMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {testConnectionMutation.isPending ? 'Testing...' : 'Test Connection'}
            </button>
            <button
              type="button"
              onClick={() => discoverResourcesMutation.mutate()}
              disabled={discoverResourcesMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {discoverResourcesMutation.isPending ? 'Discovering...' : 'Discover Resources'}
            </button>
          </div>
        )}

        {/* Test Result */}
        {testResult && (
          <div
            className={`p-4 rounded-md ${
              testResult.success
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}
          >
            <p className={`text-sm font-medium ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
              {testResult.success ? '✓ Connection successful' : '✗ Connection failed'}
            </p>
            <p className={`mt-1 text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
              {testResult.message}
            </p>
            {testResult.error && (
              <p className="mt-1 text-sm text-red-600">{testResult.error}</p>
            )}
          </div>
        )}

        {/* Discovered Resources */}
        {(discoveryResult?.resources || testResult?.discovered_resources) && (
          <div className="border border-gray-200 rounded-md">
            <button
              type="button"
              onClick={() => setShowResources(!showResources)}
              className="w-full px-4 py-2 text-left text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-t-md flex items-center justify-between"
            >
              <span>Discovered Resources</span>
              <span>{showResources ? '▼' : '▶'}</span>
            </button>
            {showResources && (
              <div className="p-4 bg-gray-50">
                <pre className="text-xs overflow-auto max-h-64">
                  {JSON.stringify(
                    discoveryResult?.resources || testResult?.discovered_resources,
                    null,
                    2
                  )}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Cancel
            </button>
          )}
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {saveMutation.isPending ? 'Saving...' : initialConfig ? 'Update Server' : 'Create Server'}
          </button>
        </div>

        {/* Error Message */}
        {saveMutation.isError && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-800">
              {saveMutation.error instanceof Error
                ? saveMutation.error.message
                : 'Failed to save server configuration'}
            </p>
          </div>
        )}
      </form>
    </div>
  )
}


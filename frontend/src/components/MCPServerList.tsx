import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  MCPServerResponse,
  mcpServerApi,
  MCPConnectionTestResponse,
  MCPResourceDiscoveryResponse,
} from '../services/api'

interface MCPServerListProps {
  onEdit: (server: MCPServerResponse) => void
  onCreate: () => void
}

export default function MCPServerList({ onEdit, onCreate }: MCPServerListProps) {
  const [serverTypeFilter, setServerTypeFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedServer, setExpandedServer] = useState<string | null>(null)

  const queryClient = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['mcp-servers', serverTypeFilter],
    queryFn: () =>
      mcpServerApi.getServers({
        server_type: serverTypeFilter || undefined,
      }),
  })

  const testConnectionMutation = useMutation({
    mutationFn: (serverId: string) => mcpServerApi.testConnection(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] })
    },
  })

  const discoverResourcesMutation = useMutation({
    mutationFn: (serverId: string) => mcpServerApi.discoverResources(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] })
    },
  })

  const enableServerMutation = useMutation({
    mutationFn: (serverId: string) => mcpServerApi.enableServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] })
    },
  })

  const disableServerMutation = useMutation({
    mutationFn: (serverId: string) => mcpServerApi.disableServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] })
    },
  })

  const deleteServerMutation = useMutation({
    mutationFn: (serverId: string) => mcpServerApi.deleteServer(serverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mcp-servers'] })
    },
  })

  const filteredServers =
    data?.servers.filter((server) => {
      const matchesType = !serverTypeFilter || server.server_type === serverTypeFilter
      const matchesSearch =
        !searchQuery ||
        server.server_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        server.endpoint_url?.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesType && matchesSearch
    }) || []

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-gray-500">Loading MCP servers...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <p className="text-red-600">Error loading MCP servers: {error.message}</p>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-5 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">MCP Servers</h2>
          <button
            onClick={onCreate}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Add Server
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex space-x-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by name or endpoint..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <select
              value={serverTypeFilter}
              onChange={(e) => setServerTypeFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">All Types</option>
              <option value="grafana">Grafana</option>
              <option value="aws">AWS</option>
              <option value="gcp">GCP</option>
              <option value="custom">Custom</option>
            </select>
          </div>
        </div>
      </div>

      {/* Server List */}
      <div className="divide-y divide-gray-200">
        {filteredServers.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500">No MCP servers found</p>
            <button
              onClick={onCreate}
              className="mt-4 text-sm text-blue-600 hover:text-blue-800"
            >
              Create your first MCP server
            </button>
          </div>
        ) : (
          filteredServers.map((server) => (
            <div key={server.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-sm font-medium text-gray-900">{server.server_name}</h3>
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                      {server.server_type}
                    </span>
                    {server.is_enabled ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        Enabled
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        Disabled
                      </span>
                    )}
                    {server.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        Connected
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                        Not Connected
                      </span>
                    )}
                  </div>
                  {server.endpoint_url && (
                    <p className="mt-1 text-sm text-gray-500">{server.endpoint_url}</p>
                  )}
                  {server.last_tested_at && (
                    <p className="mt-1 text-xs text-gray-400">
                      Last tested: {new Date(server.last_tested_at).toLocaleString()}
                      {server.last_test_status && ` (${server.last_test_status})`}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onEdit(server)}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => testConnectionMutation.mutate(server.id)}
                    disabled={testConnectionMutation.isPending}
                    className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                  >
                    Test
                  </button>
                  <button
                    onClick={() => discoverResourcesMutation.mutate(server.id)}
                    disabled={discoverResourcesMutation.isPending}
                    className="text-sm text-purple-600 hover:text-purple-800 disabled:opacity-50"
                  >
                    Discover
                  </button>
                  {server.is_enabled ? (
                    <button
                      onClick={() => disableServerMutation.mutate(server.id)}
                      disabled={disableServerMutation.isPending}
                      className="text-sm text-orange-600 hover:text-orange-800 disabled:opacity-50"
                    >
                      Disable
                    </button>
                  ) : (
                    <button
                      onClick={() => enableServerMutation.mutate(server.id)}
                      disabled={enableServerMutation.isPending}
                      className="text-sm text-green-600 hover:text-green-800 disabled:opacity-50"
                    >
                      Enable
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to delete "${server.server_name}"?`)) {
                        deleteServerMutation.mutate(server.id)
                      }
                    }}
                    disabled={deleteServerMutation.isPending}
                    className="text-sm text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Expandable Resources Section */}
              {server.discovered_resources && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() =>
                      setExpandedServer(expandedServer === server.id ? null : server.id)
                    }
                    className="text-sm text-gray-600 hover:text-gray-800 flex items-center"
                  >
                    <span className="mr-2">
                      {expandedServer === server.id ? '▼' : '▶'}
                    </span>
                    Discovered Resources
                    {server.discovered_resources &&
                      Object.keys(server.discovered_resources).length > 0 && (
                        <span className="ml-2 text-xs text-gray-400">
                          ({Object.keys(server.discovered_resources).length} categories)
                        </span>
                      )}
                  </button>
                  {expandedServer === server.id && (
                    <div className="mt-2 p-3 bg-gray-50 rounded-md">
                      <pre className="text-xs overflow-auto max-h-64">
                        {JSON.stringify(server.discovered_resources, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}


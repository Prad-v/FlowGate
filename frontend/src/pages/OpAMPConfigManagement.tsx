import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { opampConfigApi, OpAMPConfigDeployment } from '../services/api'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function OpAMPConfigManagement() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedDeployment, setSelectedDeployment] = useState<string | null>(null)

  const { data: deployments, isLoading } = useQuery({
    queryKey: ['opamp-config-deployments', MOCK_ORG_ID],
    queryFn: () => opampConfigApi.getDeployments(MOCK_ORG_ID),
    refetchInterval: 10000,
  })

  const { data: deploymentStatus } = useQuery({
    queryKey: ['deployment-status', selectedDeployment, MOCK_ORG_ID],
    queryFn: () => {
      if (!selectedDeployment) return null
      return opampConfigApi.getDeploymentStatus(selectedDeployment, MOCK_ORG_ID)
    },
    enabled: !!selectedDeployment,
    refetchInterval: 5000,
  })

  const rollbackMutation = useMutation({
    mutationFn: (deploymentId: string) => opampConfigApi.rollbackDeployment(deploymentId, MOCK_ORG_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opamp-config-deployments'] })
      setSelectedDeployment(null)
    },
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'rolled_back':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-yellow-100 text-yellow-800'
    }
  }

  if (isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">Loading deployments...</div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">OpAMP Config Management</h1>
          <p className="mt-1 text-sm text-gray-500">Manage remote configuration deployments for agents</p>
        </div>
        <button
          onClick={() => navigate('/opamp-config/create')}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Create Deployment
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {deployments && deployments.length > 0 ? (
            deployments.map((deployment) => (
              <li key={deployment.id}>
                <div className="px-4 py-4 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900 truncate">{deployment.name}</p>
                      <span className={`ml-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(deployment.status)}`}>
                        {deployment.status}
                      </span>
                    </div>
                    <div className="ml-2 flex-shrink-0 flex">
                      <button
                        onClick={() => setSelectedDeployment(deployment.id)}
                        className="mr-2 inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        View Details
                      </button>
                      {deployment.status === 'failed' && (
                        <button
                          onClick={() => rollbackMutation.mutate(deployment.id)}
                          className="inline-flex items-center px-3 py-1 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50"
                        >
                          Rollback
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 sm:flex sm:justify-between">
                    <div className="sm:flex">
                      <p className="flex items-center text-sm text-gray-500">
                        Version: {deployment.config_version} | Strategy: {deployment.rollout_strategy}
                        {deployment.canary_percentage && ` | Canary: ${deployment.canary_percentage}%`}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                      <p>Created: {new Date(deployment.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                </div>
              </li>
            ))
          ) : (
            <li className="px-4 py-8 text-center text-sm text-gray-500">No deployments found</li>
          )}
        </ul>
      </div>

      {/* Deployment Details Modal */}
      {selectedDeployment && deploymentStatus && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-gray-900">Deployment Details</h3>
              <button
                onClick={() => setSelectedDeployment(null)}
                className="text-gray-400 hover:text-gray-500"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Progress</h4>
                <div className="grid grid-cols-5 gap-4 text-sm">
                  <div>
                    <dt className="text-gray-500">Total</dt>
                    <dd className="text-gray-900 font-semibold">{deploymentStatus.progress.total}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Applied</dt>
                    <dd className="text-green-600 font-semibold">{deploymentStatus.progress.applied}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Applying</dt>
                    <dd className="text-blue-600 font-semibold">{deploymentStatus.progress.applying}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Failed</dt>
                    <dd className="text-red-600 font-semibold">{deploymentStatus.progress.failed}</dd>
                  </div>
                  <div>
                    <dt className="text-gray-500">Success Rate</dt>
                    <dd className="text-gray-900 font-semibold">{(deploymentStatus.progress.success_rate * 100).toFixed(1)}%</dd>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">Agent Status</h4>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Updated</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {deploymentStatus.agent_statuses.map((agent) => (
                        <tr key={agent.gateway_id}>
                          <td className="px-3 py-2 whitespace-nowrap text-gray-900">{agent.gateway_name}</td>
                          <td className="px-3 py-2 whitespace-nowrap">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              agent.status === 'applied' ? 'bg-green-100 text-green-800' :
                              agent.status === 'applying' ? 'bg-blue-100 text-blue-800' :
                              agent.status === 'failed' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {agent.status}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-gray-500 text-xs">
                            {agent.status_reported_at ? new Date(agent.status_reported_at).toLocaleString() : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


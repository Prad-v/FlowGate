import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { deploymentApi, templateApi, Deployment, DeploymentCreate } from '../services/api'

// Mock org_id for now - in production, get from auth context
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function Deployments() {
  const [showCreateForm, setShowCreateForm] = useState(false)
  const queryClient = useQueryClient()

  const { data: deployments, isLoading } = useQuery({
    queryKey: ['deployments', MOCK_ORG_ID],
    queryFn: () => deploymentApi.list(MOCK_ORG_ID),
  })

  const { data: templates } = useQuery({
    queryKey: ['templates', MOCK_ORG_ID],
    queryFn: () => templateApi.list(MOCK_ORG_ID),
  })

  const createMutation = useMutation({
    mutationFn: deploymentApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments', MOCK_ORG_ID] })
      setShowCreateForm(false)
    },
  })

  const rollbackMutation = useMutation({
    mutationFn: (id: string) => deploymentApi.rollback(id, MOCK_ORG_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments', MOCK_ORG_ID] })
    },
  })

  const handleCreate = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data: DeploymentCreate = {
      name: formData.get('name') as string,
      template_id: formData.get('template_id') as string,
      template_version: parseInt(formData.get('template_version') as string),
      rollout_strategy: (formData.get('rollout_strategy') as DeploymentCreate['rollout_strategy']) || 'immediate',
      canary_percentage: formData.get('canary_percentage') ? parseInt(formData.get('canary_percentage') as string) : undefined,
    }
    createMutation.mutate(data)
  }

  if (isLoading) {
    return <div className="px-4 py-6">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Deployments</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage template rollouts to gateways
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          {showCreateForm ? 'Cancel' : 'Create Deployment'}
        </button>
      </div>

      {showCreateForm && (
        <div className="mb-8 bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Create New Deployment</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                name="name"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Template</label>
              <select
                name="template_id"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="">Select a template</option>
                {templates?.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} (v{template.current_version})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Template Version</label>
              <input
                type="number"
                name="template_version"
                required
                min="1"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Rollout Strategy</label>
              <select
                name="rollout_strategy"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option value="immediate">Immediate</option>
                <option value="canary">Canary</option>
                <option value="staged">Staged</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Deployment'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {deployments?.map((deployment) => (
            <li key={deployment.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      {deployment.name}
                    </p>
                    <span
                      className={`ml-2 px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        deployment.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : deployment.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : deployment.status === 'in_progress'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {deployment.status}
                    </span>
                  </div>
                  <div className="flex space-x-2">
                    {deployment.status === 'completed' && (
                      <button
                        onClick={() => rollbackMutation.mutate(deployment.id)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Rollback
                      </button>
                    )}
                  </div>
                </div>
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      Template Version {deployment.template_version} • {deployment.rollout_strategy}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                    {deployment.started_at
                      ? `Started ${new Date(deployment.started_at).toLocaleDateString()}`
                      : `Created ${new Date(deployment.created_at).toLocaleDateString()}`}
                  </div>
                </div>
                {deployment.error_message && (
                  <div className="mt-2 text-sm text-red-600">{deployment.error_message}</div>
                )}
              </div>
            </li>
          ))}
        </ul>
        {deployments?.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No deployments found. Create your first deployment to get started.
          </div>
        )}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { securityApi } from '../services/api'
import AIHelper from '../components/AIHelper'

const MOCK_ORG_ID = '00000000-0000-0000-0000-000000000000'

export default function SoarPlaybooks() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  const { data: playbooks, isLoading: playbooksLoading } = useQuery({
    queryKey: ['soar-playbooks'],
    queryFn: async () => {
      return await securityApi.getPlaybooks()
    },
  })

  const { data: executions, isLoading: executionsLoading } = useQuery({
    queryKey: ['soar-executions', selectedStatus],
    queryFn: async () => {
      return await securityApi.getExecutions(
        undefined,
        selectedStatus !== 'all' ? selectedStatus : undefined
      )
    },
  })

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">SOAR Playbooks</h1>
        <p className="mt-2 text-sm text-gray-600">
          Manage and monitor SOAR automation playbooks and executions
        </p>
      </div>

      {/* Playbooks Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Playbooks</h2>
        {playbooksLoading ? (
          <div className="text-center text-gray-500 py-4">Loading playbooks...</div>
        ) : playbooks && playbooks.length > 0 ? (
          <div className="space-y-3">
            {playbooks.map((playbook: any) => (
              <div key={playbook.id} className="border border-gray-200 rounded-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{playbook.name}</h3>
                    {playbook.description && (
                      <p className="text-sm text-gray-500 mt-1">{playbook.description}</p>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      playbook.is_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {playbook.is_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                    <span className="text-xs text-gray-500">v{playbook.version}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">No playbooks configured</div>
        )}
      </div>

      {/* Executions Section */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Executions</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
        {executionsLoading ? (
          <div className="text-center text-gray-500 py-4">Loading executions...</div>
        ) : executions && executions.length > 0 ? (
          <div className="space-y-3">
            {executions.map((execution: any) => (
              <div key={execution.id} className="border border-gray-200 rounded-md p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-medium text-gray-900">Execution #{execution.id.slice(0, 8)}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      Trigger: {execution.trigger_type}
                      {execution.trigger_entity_id && ` - ${execution.trigger_entity_id}`}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      execution.status === 'completed' ? 'bg-green-100 text-green-800' :
                      execution.status === 'running' ? 'bg-blue-100 text-blue-800' :
                      execution.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {execution.status}
                    </span>
                  </div>
                </div>
                {execution.started_at && (
                  <div className="mt-2 text-xs text-gray-500">
                    Started: {new Date(execution.started_at).toLocaleString()}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center text-gray-500 py-4">No executions found</div>
        )}
      </div>

      {/* AI Helper */}
      <AIHelper 
        page="soar-playbooks" 
        orgId={MOCK_ORG_ID}
        context={playbooks ? `Viewing ${playbooks.length} playbooks` : undefined}
      />
    </div>
  )
}


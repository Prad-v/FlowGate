import { useQuery } from '@tanstack/react-query'
import { supervisorApi } from '../services/api'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

interface SupervisorStatusProps {
  instanceId: string
}

export default function SupervisorStatus({ instanceId }: SupervisorStatusProps) {
  const { data: status, isLoading } = useQuery({
    queryKey: ['supervisor-status', instanceId],
    queryFn: () => supervisorApi.getStatus(instanceId, MOCK_ORG_ID),
    refetchInterval: 5000,
  })

  const { data: description } = useQuery({
    queryKey: ['supervisor-description', instanceId],
    queryFn: () => supervisorApi.getAgentDescription(instanceId, MOCK_ORG_ID),
    enabled: !!instanceId,
  })

  if (isLoading) {
    return <div className="text-sm text-gray-500">Loading supervisor status...</div>
  }

  if (!status) {
    return <div className="text-sm text-gray-500">Supervisor status not available</div>
  }

  const supervisorStatus = status.supervisor_status || {}
  const health = supervisorStatus.health || {}

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-2">Supervisor Status</h4>
        <div className="bg-gray-50 rounded-md p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Management Mode:</span>
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
              {status.management_mode || 'supervisor'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">OpAMP Connection:</span>
            <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
              status.opamp_connection_status === 'connected'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              {status.opamp_connection_status || 'unknown'}
            </span>
          </div>
          {health.healthy !== undefined && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Agent Health:</span>
              <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                health.healthy
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}>
                {health.healthy ? 'Healthy' : 'Unhealthy'}
              </span>
            </div>
          )}
          {health.start_time_unix_nano && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Start Time:</span>
              <span className="text-sm text-gray-900">
                {new Date(Number(health.start_time_unix_nano) / 1000000).toLocaleString()}
              </span>
            </div>
          )}
          {health.last_error && (
            <div className="mt-2">
              <span className="text-sm text-gray-600">Last Error:</span>
              <p className="text-sm text-red-600 mt-1">{health.last_error}</p>
            </div>
          )}
        </div>
      </div>

      {description && description.agent_description && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Agent Description</h4>
          <div className="bg-gray-50 rounded-md p-3">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
              {JSON.stringify(description.agent_description, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}


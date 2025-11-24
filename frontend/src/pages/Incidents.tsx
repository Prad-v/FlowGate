import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { securityApi } from '../services/api'
import AIHelper from '../components/AIHelper'

const MOCK_ORG_ID = '00000000-0000-0000-0000-000000000000'

export default function Incidents() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents', selectedStatus],
    queryFn: async () => {
      return await securityApi.getIncidents(
        selectedStatus !== 'all' ? selectedStatus : undefined
      )
    },
  })

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Security Incidents</h1>
        <p className="mt-2 text-sm text-gray-600">
          View correlated security incidents with root cause analysis
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="new">New</option>
            <option value="investigating">Investigating</option>
            <option value="contained">Contained</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Incidents List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">Loading incidents...</div>
        ) : incidents && incidents.length > 0 ? (
          incidents.map((incident: any) => (
            <div key={incident.id} className="bg-white shadow rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{incident.title}</h3>
                  {incident.description && (
                    <p className="text-sm text-gray-600 mt-1">{incident.description}</p>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                    incident.severity === 'critical' ? 'bg-red-100 text-red-800' :
                    incident.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                    incident.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-blue-100 text-blue-800'
                  }`}>
                    {incident.severity}
                  </span>
                  <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                    incident.status === 'new' ? 'bg-blue-100 text-blue-800' :
                    incident.status === 'investigating' ? 'bg-yellow-100 text-yellow-800' :
                    incident.status === 'contained' ? 'bg-green-100 text-green-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {incident.status}
                  </span>
                </div>
              </div>
              {incident.root_cause && (
                <div className="mt-4 p-3 bg-gray-50 rounded-md">
                  <div className="text-sm font-medium text-gray-700 mb-1">Root Cause:</div>
                  <div className="text-sm text-gray-600">{incident.root_cause}</div>
                </div>
              )}
              <div className="mt-4 text-xs text-gray-500">
                Detected: {new Date(incident.detected_at).toLocaleString()}
                {incident.correlated_alerts && (
                  <span className="ml-4">Correlated Alerts: {incident.correlated_alerts.length}</span>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">No incidents found</div>
        )}
      </div>

      {/* AI Helper */}
      <AIHelper 
        page="incidents" 
        orgId={MOCK_ORG_ID}
        context={incidents ? `Viewing ${incidents.length} incidents` : undefined}
      />
    </div>
  )
}


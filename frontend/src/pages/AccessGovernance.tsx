import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { securityApi } from '../services/api'
import AIHelper from '../components/AIHelper'

const MOCK_ORG_ID = '00000000-0000-0000-0000-000000000000'

export default function AccessGovernance() {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  const { data: requests, isLoading } = useQuery({
    queryKey: ['access-requests', selectedStatus],
    queryFn: async () => {
      return await securityApi.getAccessRequests(
        selectedStatus !== 'all' ? selectedStatus : undefined
      )
    },
  })

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Access Governance</h1>
        <p className="mt-2 text-sm text-gray-600">
          Manage JITA/JITP access requests with AI-powered risk assessment
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="denied">Denied</option>
              <option value="expired">Expired</option>
            </select>
          </div>
        </div>
      </div>

      {/* Requests Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Requester</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resource</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">Loading access requests...</td>
              </tr>
            ) : requests && requests.length > 0 ? (
              requests.map((request: any) => (
                <tr key={request.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{request.requester_id}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{request.resource_id}</div>
                    <div className="text-sm text-gray-500">{request.resource_type}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {request.request_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {request.risk_score !== null && request.risk_score !== undefined ? (
                      <div className="flex items-center">
                        <div className={`w-16 h-2 bg-gray-200 rounded-full mr-2`}>
                          <div
                            className={`h-2 rounded-full ${
                              request.risk_score >= 0.7 ? 'bg-red-500' :
                              request.risk_score >= 0.5 ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${request.risk_score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-700">{(request.risk_score * 100).toFixed(0)}%</span>
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      request.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      request.status === 'approved' ? 'bg-green-100 text-green-800' :
                      request.status === 'denied' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {request.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(request.created_at).toLocaleString()}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-6 py-4 text-center text-gray-500">No access requests</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* AI Helper */}
      <AIHelper 
        page="access-governance" 
        orgId={MOCK_ORG_ID}
        context={requests ? `Viewing ${requests.length} access requests` : undefined}
      />
    </div>
  )
}


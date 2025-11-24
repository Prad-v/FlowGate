import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { securityApi } from '../services/api'
import AIHelper from '../components/AIHelper'

const MOCK_ORG_ID = '00000000-0000-0000-0000-000000000000'

export default function Personas() {
  const [selectedEntityType, setSelectedEntityType] = useState<string>('all')

  const { data: baselines, isLoading } = useQuery({
    queryKey: ['persona-baselines', selectedEntityType],
    queryFn: async () => {
      return await securityApi.getBaselines(
        selectedEntityType !== 'all' ? selectedEntityType : undefined
      )
    },
  })

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Persona Baselines</h1>
        <p className="mt-2 text-sm text-gray-600">
          Monitor behavior baselines and anomalies for users and services
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Entity Type</label>
          <select
            value={selectedEntityType}
            onChange={(e) => setSelectedEntityType(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="all">All Types</option>
            <option value="user">Users</option>
            <option value="service">Services</option>
            <option value="host">Hosts</option>
          </select>
        </div>
      </div>

      {/* Baselines List */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Entity</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Samples</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Updated</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">Loading baselines...</td>
              </tr>
            ) : baselines && baselines.length > 0 ? (
              baselines.map((baseline: any) => (
                <tr key={baseline.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{baseline.entity_id}</div>
                    {baseline.entity_name && (
                      <div className="text-sm text-gray-500">{baseline.entity_name}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {baseline.entity_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {baseline.sample_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      baseline.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {baseline.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {baseline.last_updated_at ? new Date(baseline.last_updated_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-gray-500">No baselines found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* AI Helper */}
      <AIHelper 
        page="personas" 
        orgId={MOCK_ORG_ID}
        context={baselines ? `Viewing ${baselines.length} baselines` : undefined}
      />
    </div>
  )
}


import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { templateApi } from '../services/api'

// Mock org_id for now - in production, get from auth context
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function TemplateDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: template, isLoading } = useQuery({
    queryKey: ['template', id, MOCK_ORG_ID],
    queryFn: () => templateApi.get(id!, MOCK_ORG_ID),
    enabled: !!id,
  })

  const { data: versions } = useQuery({
    queryKey: ['template-versions', id, MOCK_ORG_ID],
    queryFn: () => templateApi.getVersions(id!, MOCK_ORG_ID),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="px-4 py-6">Loading...</div>
  }

  if (!template) {
    return (
      <div className="px-4 py-6">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Template not found</h1>
          <button
            onClick={() => navigate('/templates')}
            className="text-blue-600 hover:text-blue-800"
          >
            Back to Templates
          </button>
        </div>
      </div>
    )
  }

  const defaultVersion = versions?.find((v) => v.is_active) || versions?.[versions.length - 1]

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <button
          onClick={() => navigate('/templates')}
          className="text-blue-600 hover:text-blue-800 text-sm mb-4"
        >
          ← Back to Templates
        </button>
        <h1 className="text-3xl font-bold text-gray-900">{template.name}</h1>
        {template.description && (
          <p className="mt-2 text-sm text-gray-600">{template.description}</p>
        )}
      </div>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Template Information</h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Type</dt>
            <dd className="mt-1 text-sm text-gray-900">{template.template_type}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1">
              <span
                className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                  template.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                {template.is_active ? 'Active' : 'Inactive'}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Current Version</dt>
            <dd className="mt-1 text-sm text-gray-900">v{template.current_version}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">System Template</dt>
            <dd className="mt-1">
              {template.is_system_template ? (
                <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">
                  System
                </span>
              ) : (
                <span className="text-sm text-gray-500">No</span>
              )}
            </dd>
          </div>
        </dl>
      </div>

      {defaultVersion && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Configuration (Version {defaultVersion.version})
          </h2>
          <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-sm">
            <code>{defaultVersion.config_yaml}</code>
          </pre>
        </div>
      )}
    </div>
  )
}


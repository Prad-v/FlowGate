import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templateApi, Template, TemplateCreate } from '../services/api'
import { Link } from 'react-router-dom'
import TemplateCreateModal from '../components/TemplateCreateModal'
import TemplateVersionSelector from '../components/TemplateVersionSelector'

// Mock org_id for now - in production, get from auth context
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function Templates() {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [expandedTemplate, setExpandedTemplate] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates', MOCK_ORG_ID],
    queryFn: () => templateApi.list(MOCK_ORG_ID),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => templateApi.delete(id, MOCK_ORG_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', MOCK_ORG_ID] })
    },
  })

  const toggleExpand = (templateId: string) => {
    setExpandedTemplate(expandedTemplate === templateId ? null : templateId)
  }

  if (isLoading) {
    return <div className="px-4 py-6">Loading...</div>
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Templates</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage your OTel collector configuration templates with version control
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Create Template
        </button>
      </div>

      <TemplateCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={() => {
          setShowCreateModal(false)
        }}
      />

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {templates?.map((template) => (
            <li key={template.id}>
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <p className="text-sm font-medium text-blue-600 truncate">
                      {template.name}
                    </p>
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      {template.template_type}
                    </span>
                    {template.is_system_template && (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-100 text-purple-800">
                        System
                      </span>
                    )}
                    {template.is_active ? (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                        Inactive
                      </span>
                    )}
                    {template.default_version_id && (
                      <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                        Default: v{template.current_version}
                      </span>
                    )}
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => toggleExpand(template.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      {expandedTemplate === template.id ? 'Hide Versions' : 'Show Versions'}
                    </button>
                    <Link
                      to={`/templates/${template.id}`}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      View
                    </Link>
                    <button
                      onClick={() => deleteMutation.mutate(template.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                {template.description && (
                  <p className="mt-2 text-sm text-gray-500">{template.description}</p>
                )}
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      Current Version: {template.current_version}
                    </p>
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                    Updated {new Date(template.updated_at || template.created_at).toLocaleDateString()}
                  </div>
                </div>

                {/* Version Management Section */}
                {expandedTemplate === template.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-medium text-gray-900 mb-3">Version Management</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Select Version
                        </label>
                        <TemplateVersionSelector
                          template={template}
                          showSetDefault={true}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
        {templates?.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500">
            No templates found. Create your first template to get started.
          </div>
        )}
      </div>
    </div>
  )
}

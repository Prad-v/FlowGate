import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { templateApi, TemplateVersion, Template } from '../services/api'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

interface TemplateVersionSelectorProps {
  template: Template
  selectedVersion?: number
  onVersionChange?: (version: number) => void
  showSetDefault?: boolean
}

export default function TemplateVersionSelector({
  template,
  selectedVersion,
  onVersionChange,
  showSetDefault = true,
}: TemplateVersionSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const queryClient = useQueryClient()

  const { data: versions, isLoading } = useQuery({
    queryKey: ['template-versions', template.id, MOCK_ORG_ID],
    queryFn: () => templateApi.getVersions(template.id, MOCK_ORG_ID),
    enabled: isOpen,
  })

  const setDefaultMutation = useMutation({
    mutationFn: (version: number) => templateApi.setDefaultVersion(template.id, version, MOCK_ORG_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', MOCK_ORG_ID] })
      queryClient.invalidateQueries({ queryKey: ['template-versions', template.id, MOCK_ORG_ID] })
    },
  })

  const handleSetDefault = (version: number) => {
    if (window.confirm(`Set version ${version} as the default version for this template?`)) {
      setDefaultMutation.mutate(version)
    }
  }

  // Find default version
  const defaultVersion = versions?.find((v: TemplateVersion) => v.id === template.default_version_id)
  const currentSelectedVersion = selectedVersion || defaultVersion?.version || template.current_version

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 text-left border border-gray-300 rounded-md shadow-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-700">
            Version {currentSelectedVersion}
            {defaultVersion && currentSelectedVersion === defaultVersion.version && (
              <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                Default
              </span>
            )}
          </span>
          <svg
            className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? 'transform rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none">
          {isLoading ? (
            <div className="px-4 py-2 text-sm text-gray-500">Loading versions...</div>
          ) : versions && versions.length > 0 ? (
            versions.map((version: TemplateVersion) => {
              const isDefault = version.id === template.default_version_id
              const isSelected = version.version === currentSelectedVersion

              return (
                <div
                  key={version.id}
                  className={`px-4 py-2 text-sm cursor-pointer hover:bg-gray-100 ${
                    isSelected ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => {
                    if (onVersionChange) {
                      onVersionChange(version.version)
                    }
                    setIsOpen(false)
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-gray-900">Version {version.version}</span>
                      {isDefault && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                          Default
                        </span>
                      )}
                      {isSelected && !isDefault && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                          Selected
                        </span>
                      )}
                    </div>
                    {showSetDefault && !isDefault && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleSetDefault(version.version)
                        }}
                        className="text-xs text-blue-600 hover:text-blue-800"
                        disabled={setDefaultMutation.isPending}
                      >
                        {setDefaultMutation.isPending ? 'Setting...' : 'Set as Default'}
                      </button>
                    )}
                  </div>
                  {version.description && (
                    <p className="mt-1 text-xs text-gray-500 truncate">{version.description}</p>
                  )}
                  <p className="mt-1 text-xs text-gray-400">
                    {new Date(version.created_at).toLocaleDateString()}
                  </p>
                </div>
              )
            })
          ) : (
            <div className="px-4 py-2 text-sm text-gray-500">No versions available</div>
          )}
        </div>
      )}
    </div>
  )
}


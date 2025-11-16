import { useState, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { templateApi, supervisorApi, TemplateCreate } from '../services/api'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

interface TemplateCreateModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

type TabType = 'create' | 'upload' | 'gateway'

export default function TemplateCreateModal({ isOpen, onClose, onSuccess }: TemplateCreateModalProps) {
  const [activeTab, setActiveTab] = useState<TabType>('create')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [templateType, setTemplateType] = useState<'metrics' | 'logs' | 'traces' | 'routing' | 'composite'>('composite')
  const [configYaml, setConfigYaml] = useState('')
  const [isSystemTemplate, setIsSystemTemplate] = useState(false)
  const [selectedGatewayId, setSelectedGatewayId] = useState<string>('')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [uploadPreview, setUploadPreview] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const queryClient = useQueryClient()

  // Fetch agents for gateway selection
  const { data: agents } = useQuery({
    queryKey: ['supervisor-agents', MOCK_ORG_ID],
    queryFn: () => supervisorApi.listAgents(MOCK_ORG_ID),
    enabled: isOpen && activeTab === 'gateway',
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: (data: TemplateCreate) => templateApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', MOCK_ORG_ID] })
      handleClose()
      onSuccess?.()
    },
  })

  // Create from gateway mutation
  const createFromGatewayMutation = useMutation({
    mutationFn: () => {
      if (!selectedGatewayId) {
        throw new Error('Please select a gateway')
      }
      return templateApi.createFromGateway(
        selectedGatewayId,
        name,
        description,
        templateType,
        isSystemTemplate,
        MOCK_ORG_ID
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', MOCK_ORG_ID] })
      handleClose()
      onSuccess?.()
    },
    onError: (error: any) => {
      console.error('Failed to create template from gateway:', error)
      const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to create template from gateway'
      alert(errorMessage)
    },
  })

  // Upload template mutation
  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!uploadedFile) throw new Error('No file selected')
      return templateApi.uploadTemplate(
        uploadedFile,
        name,
        description,
        templateType,
        isSystemTemplate,
        MOCK_ORG_ID
      )
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates', MOCK_ORG_ID] })
      handleClose()
      onSuccess?.()
    },
  })

  const handleClose = () => {
    setName('')
    setDescription('')
    setConfigYaml('')
    setSelectedGatewayId('')
    setUploadedFile(null)
    setUploadPreview('')
    setIsSystemTemplate(false)
    setActiveTab('create')
    onClose()
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.endsWith('.yaml') && !file.name.endsWith('.yml')) {
      alert('Please select a YAML file (.yaml or .yml)')
      return
    }

    setUploadedFile(file)
    const reader = new FileReader()
    reader.onload = (event) => {
      const content = event.target?.result as string
      setUploadPreview(content)
      setConfigYaml(content) // Also set in configYaml for preview
    }
    reader.readAsText(file)
  }

  const handleLoadFromGateway = async () => {
    if (!selectedGatewayId) {
      alert('Please select a gateway')
      return
    }

    try {
      // This will be handled by the createFromGatewayMutation
      createFromGatewayMutation.mutate()
    } catch (error) {
      alert('Failed to load config from gateway')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      alert('Please provide a template name')
      return
    }

    if (activeTab === 'create') {
      if (!configYaml.trim()) {
        alert('Please provide configuration YAML')
        return
      }
      createMutation.mutate({
        name,
        description: description || undefined,
        template_type: templateType,
        config_yaml: configYaml,
        is_system_template: isSystemTemplate,
        org_id: isSystemTemplate ? undefined : MOCK_ORG_ID,
      })
    } else if (activeTab === 'upload') {
      if (!uploadedFile) {
        alert('Please select a file to upload')
        return
      }
      uploadMutation.mutate()
    } else if (activeTab === 'gateway') {
      handleLoadFromGateway()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" onClick={handleClose}>
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white" onClick={(e) => e.stopPropagation()}>
        <div className="mt-3">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-medium text-gray-900">Create New Template</h3>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-4">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('create')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'create'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Create New
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'upload'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Upload File
              </button>
              <button
                onClick={() => setActiveTab('gateway')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'gateway'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Load from Gateway
              </button>
            </nav>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Common fields */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Production Config Template"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Template description..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Type</label>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="metrics">Metrics</option>
                  <option value="logs">Logs</option>
                  <option value="traces">Traces</option>
                  <option value="routing">Routing</option>
                  <option value="composite">Composite</option>
                </select>
              </div>

              <div className="flex items-center pt-6">
                <input
                  type="checkbox"
                  id="is-system-template"
                  checked={isSystemTemplate}
                  onChange={(e) => setIsSystemTemplate(e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is-system-template" className="ml-2 block text-sm text-gray-900">
                  System Template (Global)
                </label>
              </div>
            </div>

            {/* Tab-specific content */}
            {activeTab === 'create' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Configuration YAML *</label>
                <textarea
                  value={configYaml}
                  onChange={(e) => setConfigYaml(e.target.value)}
                  rows={15}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                  placeholder="receivers:&#10;  otlp:&#10;    protocols:&#10;      grpc:&#10;        endpoint: 0.0.0.0:4317"
                  required
                />
              </div>
            )}

            {activeTab === 'upload' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Upload YAML File *</label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          accept=".yaml,.yml"
                          className="sr-only"
                          ref={fileInputRef}
                          onChange={handleFileSelect}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">YAML files only (.yaml, .yml)</p>
                    {uploadedFile && (
                      <p className="text-sm text-gray-600 mt-2">Selected: {uploadedFile.name}</p>
                    )}
                  </div>
                </div>
                {uploadPreview && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preview</label>
                    <textarea
                      value={uploadPreview}
                      readOnly
                      rows={10}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 font-mono text-sm"
                    />
                  </div>
                )}
              </div>
            )}

            {activeTab === 'gateway' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Gateway *</label>
                <select
                  value={selectedGatewayId}
                  onChange={(e) => setSelectedGatewayId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select a gateway...</option>
                  {agents?.map((agent: any) => (
                    <option key={agent.instance_id || agent.gateway_id || agent.id} value={agent.gateway_id || agent.id}>
                      {agent.name || agent.instance_id} ({agent.instance_id})
                    </option>
                  ))}
                </select>
                <p className="mt-2 text-sm text-gray-500">
                  This will load the effective configuration currently running on the selected gateway.
                </p>
              </div>
            )}

            {/* Submit buttons */}
            <div className="flex justify-end space-x-3 pt-4 border-t">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={
                  createMutation.isPending ||
                  uploadMutation.isPending ||
                  createFromGatewayMutation.isPending
                }
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {createMutation.isPending || uploadMutation.isPending || createFromGatewayMutation.isPending
                  ? 'Creating...'
                  : 'Create Template'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}


import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { opampConfigApi, agentTagApi, ConfigValidationResult, templateApi, Template, TemplateVersion } from '../services/api'
import TagSelector from '../components/TagSelector'
import TemplateVersionSelector from '../components/TemplateVersionSelector'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function CreateConfigDeployment() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [name, setName] = useState('')
  const [configYaml, setConfigYaml] = useState('')
  const [rolloutStrategy, setRolloutStrategy] = useState<'immediate' | 'canary' | 'staged'>('immediate')
  const [canaryPercentage, setCanaryPercentage] = useState(10)
  const [targetTags, setTargetTags] = useState<string[]>([])
  const [ignoreFailures, setIgnoreFailures] = useState(false)
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null)
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)
  const [validationResult, setValidationResult] = useState<ConfigValidationResult | null>(null)

  const { data: allTags } = useQuery({
    queryKey: ['all-tags', MOCK_ORG_ID],
    queryFn: () => agentTagApi.getAllTags(MOCK_ORG_ID),
  })

  const { data: templates } = useQuery({
    queryKey: ['templates', MOCK_ORG_ID],
    queryFn: () => templateApi.list(MOCK_ORG_ID),
  })

  const { data: selectedTemplate } = useQuery({
    queryKey: ['template', selectedTemplateId, MOCK_ORG_ID],
    queryFn: () => selectedTemplateId ? templateApi.get(selectedTemplateId, MOCK_ORG_ID) : null,
    enabled: !!selectedTemplateId,
  })

  const { data: templateVersions } = useQuery({
    queryKey: ['template-versions', selectedTemplateId, MOCK_ORG_ID],
    queryFn: () => selectedTemplateId ? templateApi.getVersions(selectedTemplateId, MOCK_ORG_ID) : [],
    enabled: !!selectedTemplateId,
  })

  const validateMutation = useMutation({
    mutationFn: (yaml: string) => opampConfigApi.validateConfig(yaml),
    onSuccess: (result) => {
      setValidationResult(result)
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => opampConfigApi.createDeployment(MOCK_ORG_ID, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opamp-config-deployments'] })
      navigate('/opamp-config')
    },
  })

  // Load config from selected template and version
  const loadTemplateConfig = async (templateId: string, version?: number) => {
    try {
      const template = await templateApi.get(templateId, MOCK_ORG_ID)
      if (!template) {
        alert('Template not found')
        return
      }

      // Get versions if not provided
      const versions = await templateApi.getVersions(templateId, MOCK_ORG_ID)
      if (!versions || versions.length === 0) {
        alert('No versions found for this template')
        return
      }

      // Determine which version to use
      let targetVersion: TemplateVersion | undefined
      if (version) {
        targetVersion = versions.find((v: TemplateVersion) => v.version === version)
      } else {
        // Use default version if available, otherwise use latest
        if (template.default_version_id) {
          targetVersion = versions.find((v: TemplateVersion) => v.id === template.default_version_id)
        }
        if (!targetVersion) {
          // Use latest version
          targetVersion = versions.sort((a: TemplateVersion, b: TemplateVersion) => b.version - a.version)[0]
        }
      }

      if (targetVersion) {
        setConfigYaml(targetVersion.config_yaml)
        setSelectedVersion(targetVersion.version)
      } else {
        alert('Version not found')
      }
    } catch (error) {
      alert('Failed to load template config')
    }
  }

  const handleTemplateChange = (templateId: string) => {
    setSelectedTemplateId(templateId)
    setSelectedVersion(null)
    setConfigYaml('')
    if (templateId) {
      loadTemplateConfig(templateId)
    }
  }

  const handleVersionChange = (version: number) => {
    setSelectedVersion(version)
    if (selectedTemplateId) {
      loadTemplateConfig(selectedTemplateId, version)
    }
  }

  const handleValidate = () => {
    if (configYaml.trim()) {
      validateMutation.mutate(configYaml)
    }
  }

  const handleDeploy = () => {
    if (!name.trim() || !configYaml.trim()) {
      alert('Please provide a name and configuration')
      return
    }

    if (!validationResult?.is_valid && !ignoreFailures) {
      alert('Configuration validation failed. Please fix errors or enable "Ignore Validation Failures"')
      return
    }

    createMutation.mutate({
      name,
      config_yaml: configYaml,
      rollout_strategy: rolloutStrategy,
      canary_percentage: rolloutStrategy === 'canary' ? canaryPercentage : undefined,
      target_tags: targetTags.length > 0 ? targetTags : undefined,
      ignore_failures: ignoreFailures,
    })
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create Config Deployment</h1>
        <p className="mt-1 text-sm text-gray-500">Deploy configuration to agents via OpAMP</p>
      </div>

      <div className="bg-white shadow rounded-lg p-6 space-y-6">
        {/* Basic Info */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Deployment Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Production Config v2.0"
          />
        </div>

        {/* Template Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Template
          </label>
          <select
            value={selectedTemplateId || ''}
            onChange={(e) => handleTemplateChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a template...</option>
            {templates?.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name} {template.is_system_template ? '(System)' : ''} - v{template.current_version}
              </option>
            ))}
          </select>
        </div>

        {/* Version Selector (shown when template is selected) */}
        {selectedTemplate && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Version (Default: {selectedTemplate.default_version_id ? 'v' + (templateVersions?.find((v: TemplateVersion) => v.id === selectedTemplate.default_version_id)?.version || selectedTemplate.current_version) : 'v' + selectedTemplate.current_version})
            </label>
            <TemplateVersionSelector
              template={selectedTemplate}
              selectedVersion={selectedVersion || undefined}
              onVersionChange={handleVersionChange}
              showSetDefault={false}
            />
            <p className="mt-2 text-sm text-gray-500">
              The default version will be used automatically. You can override it by selecting a different version above.
            </p>
          </div>
        )}

        {/* YAML Editor */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Configuration YAML
            </label>
            <button
              onClick={handleValidate}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              Validate
            </button>
          </div>
          <textarea
            value={configYaml}
            onChange={(e) => setConfigYaml(e.target.value)}
            rows={20}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm font-mono text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="receivers:&#10;  otlp:&#10;    protocols:&#10;      grpc:&#10;        endpoint: 0.0.0.0:4317&#10;..."
          />
          
          {/* Validation Results */}
          {validationResult && (
            <div className={`mt-2 p-3 rounded-md ${validationResult.is_valid ? 'bg-green-50' : 'bg-red-50'}`}>
              <div className="text-sm font-medium mb-2">
                {validationResult.is_valid ? '✓ Configuration is valid' : '✗ Configuration has errors'}
              </div>
              {validationResult.errors.length > 0 && (
                <div className="text-sm text-red-700">
                  <div className="font-medium mb-1">Errors:</div>
                  <ul className="list-disc list-inside space-y-1">
                    {validationResult.errors.map((error, idx) => (
                      <li key={idx}>{error.field ? `${error.field}: ` : ''}{error.message}</li>
                    ))}
                  </ul>
                </div>
              )}
              {validationResult.warnings.length > 0 && (
                <div className="text-sm text-yellow-700 mt-2">
                  <div className="font-medium mb-1">Warnings:</div>
                  <ul className="list-disc list-inside space-y-1">
                    {validationResult.warnings.map((warning, idx) => (
                      <li key={idx}>{warning.field ? `${warning.field}: ` : ''}{warning.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Rollout Strategy */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rollout Strategy
          </label>
          <select
            value={rolloutStrategy}
            onChange={(e) => setRolloutStrategy(e.target.value as any)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="immediate">Immediate (All agents at once)</option>
            <option value="canary">Canary (Percentage-based)</option>
            <option value="staged">Staged (Manual phases)</option>
          </select>
        </div>

        {/* Canary Percentage */}
        {rolloutStrategy === 'canary' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Canary Percentage: {canaryPercentage}%
            </label>
            <input
              type="range"
              min="1"
              max="100"
              value={canaryPercentage}
              onChange={(e) => setCanaryPercentage(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
        )}

        {/* Target Tags */}
        <TagSelector
          selectedTags={targetTags}
          onTagsChange={setTargetTags}
          allTags={allTags}
          showAllOption={true}
        />

        {/* Ignore Failures */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="ignore-failures"
            checked={ignoreFailures}
            onChange={(e) => setIgnoreFailures(e.target.checked)}
            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
          />
          <label htmlFor="ignore-failures" className="ml-2 block text-sm text-gray-900">
            Ignore Validation Failures
          </label>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            onClick={() => navigate('/opamp-config')}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleDeploy}
            disabled={createMutation.isPending}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Deploying...' : 'Deploy'}
          </button>
        </div>
      </div>
    </div>
  )
}


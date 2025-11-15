import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { supervisorApi } from '../services/api'

const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

interface SupervisorConfigEditorProps {
  instanceId: string
  currentConfig?: string
  onSuccess?: () => void
}

export default function SupervisorConfigEditor({
  instanceId,
  currentConfig,
  onSuccess,
}: SupervisorConfigEditorProps) {
  const [configYaml, setConfigYaml] = useState(currentConfig || '')
  const queryClient = useQueryClient()

  const { data: effectiveConfig } = useQuery({
    queryKey: ['supervisor-effective-config', instanceId],
    queryFn: () => supervisorApi.getEffectiveConfig(instanceId, MOCK_ORG_ID),
    enabled: !!instanceId,
  })

  const pushMutation = useMutation({
    mutationFn: (yaml: string) => supervisorApi.pushConfig(instanceId, yaml, MOCK_ORG_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supervisor-effective-config', instanceId] })
      queryClient.invalidateQueries({ queryKey: ['supervisor-status', instanceId] })
      if (onSuccess) {
        onSuccess()
      }
    },
  })

  const handleSave = () => {
    if (!configYaml.trim()) {
      alert('Configuration cannot be empty')
      return
    }
    pushMutation.mutate(configYaml)
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Configuration YAML
        </label>
        <textarea
          value={configYaml}
          onChange={(e) => setConfigYaml(e.target.value)}
          rows={15}
          className="w-full font-mono text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="receivers:&#10;  otlp:&#10;    protocols:&#10;      grpc:&#10;        endpoint: 0.0.0.0:4317&#10;..."
        />
      </div>

      {effectiveConfig && effectiveConfig.config_yaml && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Effective Config (Currently Running)</h4>
          <div className="bg-gray-50 rounded-md p-3 max-h-64 overflow-auto">
            <pre className="text-xs text-gray-700 whitespace-pre-wrap">
              {effectiveConfig.config_yaml}
            </pre>
          </div>
        </div>
      )}

      {pushMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-md p-3">
          <p className="text-sm text-red-800">
            Error: {pushMutation.error instanceof Error ? pushMutation.error.message : 'Failed to push configuration'}
          </p>
        </div>
      )}

      {pushMutation.isSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-md p-3">
          <p className="text-sm text-green-800">Configuration pushed successfully!</p>
        </div>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={pushMutation.isPending || !configYaml.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {pushMutation.isPending ? 'Pushing...' : 'Save and Send to Agent'}
        </button>
      </div>
    </div>
  )
}


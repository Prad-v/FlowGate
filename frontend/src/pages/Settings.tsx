import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { settingsApi } from '../services/api'

// Mock org_id for now - in production, get from auth context
const MOCK_ORG_ID = '8057ca8e-4f71-4a19-b821-5937f129a0ec'

export default function Settings() {
  const queryClient = useQueryClient()
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => settingsApi.get(),
  })

  const updateMutation = useMutation({
    mutationFn: (mode: string) => settingsApi.update({ gateway_management_mode: mode }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      setSaveMessage('Settings saved successfully!')
      setTimeout(() => setSaveMessage(null), 3000)
    },
    onError: (error: any) => {
      setSaveMessage(`Error saving settings: ${error.message || 'Unknown error'}`)
      setTimeout(() => setSaveMessage(null), 5000)
    },
  })

  const handleModeChange = (mode: 'supervisor' | 'extension') => {
    updateMutation.mutate(mode)
  }

  if (isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">
          <div className="text-gray-500">Loading settings...</div>
        </div>
      </div>
    )
  }

  const currentMode = settings?.gateway_management_mode || 'supervisor'

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-600">
          Configure FlowGate system settings
        </p>
      </div>

      {saveMessage && (
        <div className={`mb-6 rounded-md p-4 ${
          saveMessage.includes('Error')
            ? 'bg-red-50 border border-red-200'
            : 'bg-green-50 border border-green-200'
        }`}>
          <p className={`text-sm ${
            saveMessage.includes('Error')
              ? 'text-red-800'
              : 'text-green-800'
          }`}>
            {saveMessage}
          </p>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-5 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Gateway Management</h2>
          <p className="mt-1 text-sm text-gray-500">
            Choose how gateways are managed: Supervisor mode (recommended) or Extension mode
          </p>
        </div>

        <div className="px-6 py-5">
          <div className="space-y-4">
            <div>
              <label className="text-base font-medium text-gray-900">
                Management Mode
              </label>
              <p className="text-sm text-gray-500 mt-1">
                Select the default management mode for new gateways
              </p>
            </div>

            <div className="mt-4 space-y-4">
              {/* Supervisor Mode Option */}
              <div
                className={`relative flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  currentMode === 'supervisor'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleModeChange('supervisor')}
              >
                <div className="flex items-center h-5">
                  <input
                    type="radio"
                    name="management_mode"
                    value="supervisor"
                    checked={currentMode === 'supervisor'}
                    onChange={() => handleModeChange('supervisor')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                </div>
                <div className="ml-3 flex-1">
                  <label className="font-medium text-gray-900 cursor-pointer">
                    Supervisor Mode (Recommended)
                  </label>
                  <p className="text-sm text-gray-500 mt-1">
                    Uses OpAMP Supervisor to manage collector lifecycle. Provides enhanced status reporting,
                    automatic restart on failure, and better process monitoring.
                  </p>
                  <div className="mt-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                      Default
                    </span>
                  </div>
                </div>
              </div>

              {/* Extension Mode Option */}
              <div
                className={`relative flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  currentMode === 'extension'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => handleModeChange('extension')}
              >
                <div className="flex items-center h-5">
                  <input
                    type="radio"
                    name="management_mode"
                    value="extension"
                    checked={currentMode === 'extension'}
                    onChange={() => handleModeChange('extension')}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                  />
                </div>
                <div className="ml-3 flex-1">
                  <label className="font-medium text-gray-900 cursor-pointer">
                    Extension Mode
                  </label>
                  <p className="text-sm text-gray-500 mt-1">
                    Uses OpAMP extension built directly into the collector. Provides direct OpAMP protocol
                    communication with minimal overhead.
                  </p>
                </div>
              </div>
            </div>

            {updateMutation.isPending && (
              <div className="mt-4 text-sm text-gray-500">
                Saving settings...
              </div>
            )}
          </div>
        </div>

        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-lg">
          <div className="text-sm text-gray-600">
            <p className="font-medium mb-1">Note:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>This setting applies to new gateway registrations</li>
              <li>Existing gateways will continue using their current mode</li>
              <li>To change an existing gateway's mode, restart it with the appropriate configuration</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}


import React, { useState, useEffect, useCallback } from 'react'
import { useMutation } from '@tanstack/react-query'
import { aiSettingsApi, AIProviderConfig } from '../services/api'

interface AIProviderConfigProps {
  initialConfig?: AIProviderConfig | null
  onSave?: () => void
}

export default function AIProviderConfigComponent({ initialConfig, onSave }: AIProviderConfigProps) {
  const [providerType, setProviderType] = useState<AIProviderConfig['provider_type']>('litellm')
  const [providerName, setProviderName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [endpoint, setEndpoint] = useState('')
  const [model, setModel] = useState('')
  const [isActive, setIsActive] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [customConfig, setCustomConfig] = useState('{}')
  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [loadingModels, setLoadingModels] = useState(false)
  const [modelsError, setModelsError] = useState<string | null>(null)

  useEffect(() => {
    if (initialConfig) {
      setProviderType(initialConfig.provider_type)
      setProviderName(initialConfig.provider_name)
      setApiKey(initialConfig.api_key || '')
      setEndpoint(initialConfig.endpoint || '')
      setModel(initialConfig.model || '')
      setIsActive(initialConfig.is_active)
      setCustomConfig(JSON.stringify(initialConfig.config || {}, null, 2))
    }
  }, [initialConfig])

  const updateMutation = useMutation({
    mutationFn: (config: AIProviderConfig) => aiSettingsApi.update(config),
    onSuccess: () => {
      if (onSave) onSave()
      setTestResult({ success: true, message: 'Configuration saved successfully!' })
      setTimeout(() => setTestResult(null), 3000)
    },
    onError: (error: any) => {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Failed to save configuration',
      })
      setTimeout(() => setTestResult(null), 5000)
    },
  })

  const testMutation = useMutation({
    mutationFn: (config: AIProviderConfig) => aiSettingsApi.test(config),
    onSuccess: (result) => {
      setTestResult(result)
      setTimeout(() => setTestResult(null), 5000)
    },
    onError: (error: any) => {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || error.message || 'Connection test failed',
      })
      setTimeout(() => setTestResult(null), 5000)
    },
  })

  const fetchModels = useCallback(async () => {
    if (!apiKey || (providerType !== 'openai' && providerType !== 'anthropic' && !endpoint)) {
      setAvailableModels([])
      return
    }

    setLoadingModels(true)
    setModelsError(null)

    let configObj = {}
    try {
      configObj = JSON.parse(customConfig)
    } catch {
      configObj = {}
    }

    const config: AIProviderConfig = {
      provider_type: providerType,
      provider_name: providerName || `${providerType}-config`,
      api_key: apiKey,
      endpoint: providerType === 'litellm' || providerType === 'custom' ? endpoint : undefined,
      model: model || undefined,
      config: configObj,
      is_active: isActive,
    }

    try {
      const result = await aiSettingsApi.getModels(config)
      if (result.success) {
        setAvailableModels(result.models || [])
        setModelsError(null)
      } else {
        setAvailableModels([])
        setModelsError(result.message || 'Failed to fetch models')
      }
    } catch (error: any) {
      setAvailableModels([])
      setModelsError(error.response?.data?.detail || error.message || 'Failed to fetch models')
    } finally {
      setLoadingModels(false)
    }
  }, [apiKey, providerType, endpoint, providerName, model, customConfig, isActive])

  // Auto-fetch models when API key and required fields are filled
  useEffect(() => {
    const timer = setTimeout(() => {
      if (apiKey && (providerType === 'openai' || providerType === 'anthropic' || (endpoint && (providerType === 'litellm' || providerType === 'custom')))) {
        fetchModels()
      } else {
        setAvailableModels([])
      }
    }, 1000) // Debounce for 1 second

    return () => clearTimeout(timer)
  }, [apiKey, providerType, endpoint, fetchModels])

  const handleSave = () => {
    let configObj = {}
    try {
      configObj = JSON.parse(customConfig)
    } catch (e) {
      setTestResult({ success: false, message: 'Invalid JSON in custom config' })
      return
    }

    const config: AIProviderConfig = {
      provider_type: providerType,
      provider_name: providerName || `${providerType}-config`,
      api_key: apiKey,
      endpoint: providerType === 'litellm' || providerType === 'custom' ? endpoint : undefined,
      model: model || undefined,
      config: configObj,
      is_active: isActive,
    }

    updateMutation.mutate(config)
  }

  const handleTest = () => {
    let configObj = {}
    try {
      configObj = JSON.parse(customConfig)
    } catch (e) {
      setTestResult({ success: false, message: 'Invalid JSON in custom config' })
      return
    }

    const config: AIProviderConfig = {
      provider_type: providerType,
      provider_name: providerName || `${providerType}-config`,
      api_key: apiKey,
      endpoint: providerType === 'litellm' || providerType === 'custom' ? endpoint : undefined,
      model: model || undefined,
      config: configObj,
      is_active: isActive,
    }

    testMutation.mutate(config)
  }

  const maskApiKey = (key: string) => {
    if (!key || key.length <= 4) return key
    return '*'.repeat(key.length - 4) + key.slice(-4)
  }

  return (
    <div className="space-y-6">
      {testResult && (
        <div
          className={`rounded-md p-4 ${
            testResult.success
              ? 'bg-green-50 border border-green-200'
              : 'bg-red-50 border border-red-200'
          }`}
        >
          <p className={`text-sm ${testResult.success ? 'text-green-800' : 'text-red-800'}`}>
            {testResult.message}
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Provider Type <span className="text-red-500">*</span>
        </label>
        <select
          value={providerType}
          onChange={(e) => setProviderType(e.target.value as AIProviderConfig['provider_type'])}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="litellm">LiteLLM</option>
          <option value="openai">OpenAI (Direct)</option>
          <option value="anthropic">Anthropic (Direct)</option>
          <option value="custom">Custom</option>
        </select>
        <p className="mt-1 text-xs text-gray-500">
          {providerType === 'litellm' && 'LiteLLM provides a unified interface to multiple LLM providers'}
          {providerType === 'openai' && 'Direct connection to OpenAI API'}
          {providerType === 'anthropic' && 'Direct connection to Anthropic API'}
          {providerType === 'custom' && 'Custom LLM provider endpoint'}
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Provider Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={providerName}
          onChange={(e) => setProviderName(e.target.value)}
          placeholder="e.g., production-litellm"
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          API Key <span className="text-red-500">*</span>
        </label>
        <div className="relative">
          <input
            type={showApiKey ? 'text' : 'password'}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter API key"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
          />
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className="absolute right-2 top-2 text-xs text-gray-500 hover:text-gray-700"
          >
            {showApiKey ? 'Hide' : 'Show'}
          </button>
        </div>
        {initialConfig?.api_key && !apiKey && (
          <p className="mt-1 text-xs text-gray-500">Current: {maskApiKey(initialConfig.api_key)}</p>
        )}
      </div>

      {(providerType === 'litellm' || providerType === 'custom') && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Endpoint URL <span className="text-red-500">*</span>
          </label>
          <input
            type="url"
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            placeholder="https://api.example.com/v1"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <p className="mt-1 text-xs text-gray-500">
            Full URL to the {providerType === 'litellm' ? 'LiteLLM' : 'custom'} API endpoint
          </p>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-1">
          <label className="block text-sm font-medium text-gray-700">Model</label>
          {loadingModels && (
            <span className="text-xs text-gray-500">Loading models...</span>
          )}
          {!loadingModels && availableModels.length > 0 && (
            <span className="text-xs text-green-600">{availableModels.length} models available</span>
          )}
        </div>
        {availableModels.length > 0 ? (
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select a model...</option>
            {availableModels.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder={loadingModels ? "Loading models..." : "e.g., gpt-4, claude-3-opus"}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loadingModels}
          />
        )}
        {modelsError && (
          <p className="mt-1 text-xs text-red-500">{modelsError}</p>
        )}
        {!modelsError && !loadingModels && (
          <p className="mt-1 text-xs text-gray-500">
            {availableModels.length > 0
              ? 'Model identifier (can be changed per request)'
              : 'Model identifier (optional, can be set per request). Enter API key to auto-load models.'}
          </p>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Additional Configuration (JSON)</label>
        <textarea
          value={customConfig}
          onChange={(e) => setCustomConfig(e.target.value)}
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder='{"temperature": 0.7, "max_tokens": 1000}'
        />
        <p className="mt-1 text-xs text-gray-500">
          Additional provider-specific configuration (temperature, max_tokens, etc.)
        </p>
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="is_active"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
        />
        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
          Set as active provider
        </label>
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleTest}
          disabled={testMutation.isPending || !apiKey || (providerType !== 'openai' && providerType !== 'anthropic' && !endpoint)}
          className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testMutation.isPending ? 'Testing...' : 'Test Connection'}
        </button>
        <button
          onClick={handleSave}
          disabled={updateMutation.isPending || !providerName || !apiKey || (providerType !== 'openai' && providerType !== 'anthropic' && !endpoint)}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  )
}


import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { logTransformationApi, LogTransformRequest } from '../services/api'
import LogFormatSelector from '../components/LogFormatSelector'

type SourceMode = 'template' | 'custom'

export default function LogTransformer() {
  const [sourceMode, setSourceMode] = useState<SourceMode>('template')
  const [sourceFormat, setSourceFormat] = useState<string | null>(null)
  const [customLogs, setCustomLogs] = useState('')
  
  // Load sample logs when format template is selected
  const handleSourceFormatChange = async (formatName: string | null) => {
    setSourceFormat(formatName)
    if (formatName && sourceMode === 'template') {
      try {
        const format = await logTransformationApi.getFormat(formatName)
        if (format.sample_logs) {
          setCustomLogs(format.sample_logs)
        }
      } catch (error) {
        console.error('Failed to load format template:', error)
        // Don't clear customLogs if there's an error
      }
    }
  }
  const [targetMode, setTargetMode] = useState<'json' | 'ai_prompt'>('json')
  const [targetJson, setTargetJson] = useState('')
  const [aiPrompt, setAiPrompt] = useState('')
  const [generatedTargetJson, setGeneratedTargetJson] = useState('')
  const [isGeneratingTarget, setIsGeneratingTarget] = useState(false)
  const [generatedConfig, setGeneratedConfig] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  const transformMutation = useMutation({
    mutationFn: (request: LogTransformRequest) => logTransformationApi.transformLogs(request),
    onSuccess: (data) => {
      setGeneratedConfig(data.otel_config)
      // If we have a config (even with warnings), consider it successful
      if (data.otel_config && data.otel_config.trim().length > 0) {
        setValidationResult({ 
          valid: data.errors.length === 0, 
          errors: data.errors, 
          warnings: data.warnings 
        })
      } else {
        // Only show as error if no config was generated
        setValidationResult({ 
          valid: false, 
          errors: data.errors.length > 0 ? data.errors : ['Failed to generate config'], 
          warnings: data.warnings 
        })
      }
    },
    onError: (error: any) => {
      setValidationResult({
        valid: false,
        errors: [error.response?.data?.detail || error.message || 'Failed to generate config'],
        warnings: [],
      })
    },
  })

  const generateTargetJsonMutation = useMutation({
    mutationFn: (request: { source_format: string | null; sample_logs: string; ai_prompt: string }) =>
      logTransformationApi.generateTargetJson(request),
    onSuccess: (data) => {
      if (data.success && data.target_json) {
        setGeneratedTargetJson(data.target_json)
        setTargetJson(data.target_json)
        // Don't switch mode automatically - let user decide
      } else {
        alert(`Failed to generate target JSON: ${data.errors.join(', ')}`)
      }
    },
    onError: (error: any) => {
      alert(`Failed to generate target JSON: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleGenerateTargetJson = () => {
    if (!aiPrompt.trim()) {
      alert('Please provide an AI prompt describing your desired output structure')
      return
    }

    if (!customLogs.trim()) {
      alert('Please provide sample logs for context')
      return
    }

    setIsGeneratingTarget(true)
    generateTargetJsonMutation.mutate({
      source_format: sourceFormat,
      sample_logs: customLogs,
      ai_prompt: aiPrompt,
    }, {
      onSettled: () => {
        setIsGeneratingTarget(false)
      }
    })
  }

  const handleGenerate = () => {
    // Determine sample logs based on source mode
    let sampleLogs = ''
    let sourceFormatForRequest: string | null = null

    if (sourceMode === 'template') {
      if (!sourceFormat) {
        alert('Please select a source format')
        return
      }
      sourceFormatForRequest = sourceFormat
      if (!customLogs.trim()) {
        alert('Please provide sample logs')
        return
      }
      sampleLogs = customLogs
    } else {
      // Custom mode
      if (!customLogs.trim()) {
        alert('Please provide sample logs')
        return
      }
      sampleLogs = customLogs
      sourceFormatForRequest = null
    }

    // Determine target JSON based on mode
    let targetJsonForRequest: string | null = null
    let aiPromptForRequest: string | null = null

    if (targetMode === 'json') {
      if (!targetJson.trim()) {
        alert('Please provide target JSON structure')
        return
      }
      targetJsonForRequest = targetJson
    } else {
      // AI prompt mode
      if (!aiPrompt.trim()) {
        alert('Please provide an AI prompt describing your desired output structure')
        return
      }
      aiPromptForRequest = aiPrompt
      // If we have a generated target JSON, use it; otherwise AI will generate it
      if (generatedTargetJson.trim()) {
        targetJsonForRequest = generatedTargetJson
      }
    }

    transformMutation.mutate({
      source_format: sourceFormatForRequest,
      destination_format: null,
      sample_logs: sampleLogs,
      target_json: targetJsonForRequest,
      ai_prompt: aiPromptForRequest,
    })
  }

  const handleValidate = async () => {
    if (!generatedConfig) return
    setIsValidating(true)
    try {
      const result = await logTransformationApi.validateConfig({
        config: generatedConfig,
        sample_logs: customLogs || '',
      })
      setValidationResult(result)
    } catch (error) {
      setValidationResult({ valid: false, errors: ['Validation failed'] })
    } finally {
      setIsValidating(false)
    }
  }

  const handleDryRun = async () => {
    if (!generatedConfig || !customLogs) return
    setIsValidating(true)
    try {
      const result = await logTransformationApi.dryRun({
        config: generatedConfig,
        sample_logs: customLogs,
      })
      if (result.success) {
        setValidationResult({
          valid: true,
          transformed_logs: result.transformed_logs,
          errors: result.errors,
        })
      } else {
        setValidationResult({ valid: false, errors: result.errors })
      }
    } catch (error) {
      setValidationResult({ valid: false, errors: ['Dry run failed'] })
    } finally {
      setIsValidating(false)
    }
  }

  // Get sample logs from selected format template
  const getSampleLogsForFormat = () => {
    // This would require fetching the format template
    // For now, return empty - user will provide their own
    return ''
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Log Transformer Studio</h1>
        <p className="mt-2 text-sm text-gray-600">
          Transform unstructured logs into structured JSON using AI-assisted OTel config generation
        </p>
      </div>

      {/* Source Configuration Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Source Configuration</h2>
          
          {/* Source Mode Toggle */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Source Type</label>
            <div className="flex space-x-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="sourceMode"
                  value="template"
                  checked={sourceMode === 'template'}
                  onChange={(e) => {
                    setSourceMode(e.target.value as SourceMode)
                    if (e.target.value === 'custom') {
                      setSourceFormat(null)
                    }
                  }}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Select Format Template</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="sourceMode"
                  value="custom"
                  checked={sourceMode === 'custom'}
                  onChange={(e) => {
                    setSourceMode(e.target.value as SourceMode)
                    if (e.target.value === 'custom') {
                      setSourceFormat(null)
                    }
                  }}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Custom Logs</span>
              </label>
            </div>
          </div>

          {/* Format Selector (when template mode) */}
            {sourceMode === 'template' && (
              <div className="mb-4">
                <LogFormatSelector
                  value={sourceFormat}
                  onChange={handleSourceFormatChange}
                  formatType="source"
                  label="Source Format"
                  placeholder="Select source log format..."
                  showPreview={true}
                />
              </div>
            )}

          {/* Sample Logs Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sample Logs {sourceMode === 'template' && sourceFormat && '(You can modify the template sample or provide your own)'}
            </label>
            <textarea
              value={customLogs}
              onChange={(e) => setCustomLogs(e.target.value)}
              rows={8}
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm"
              placeholder={
                sourceMode === 'template'
                  ? 'Select a format template above, or provide your own sample logs here...'
                  : 'Paste your log entries here (one per line or multiple lines)...'
              }
            />
            {sourceMode === 'template' && sourceFormat && (
              <p className="mt-2 text-xs text-gray-500">
                💡 Tip: The format template provides a parser configuration. Provide your actual log samples above for AI analysis.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Destination Configuration Section */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Target Output Structure</h2>
        
        {/* Target Mode Toggle */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Target Definition Method</label>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="targetMode"
                value="json"
                checked={targetMode === 'json'}
                onChange={(e) => setTargetMode(e.target.value as 'json' | 'ai_prompt')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Provide Target JSON</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="targetMode"
                value="ai_prompt"
                checked={targetMode === 'ai_prompt'}
                onChange={(e) => setTargetMode(e.target.value as 'json' | 'ai_prompt')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Use AI Prompt</span>
            </label>
          </div>
        </div>

        {/* Target JSON Mode */}
        {targetMode === 'json' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Structured JSON <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Specify the desired JSON structure for your transformed logs. AI will analyze your source logs and generate transformation rules to match this structure.
            </p>
            <textarea
              value={targetJson}
              onChange={(e) => setTargetJson(e.target.value)}
              rows={8}
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm"
              placeholder='{"method": "GET", "path": "/index.html", "status": 200, "timestamp": "2024-01-02T10:30:45Z"}'
              required
            />
            {generatedTargetJson && (
              <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md">
                <p className="text-xs text-green-800 font-medium mb-1">✓ Generated from AI Prompt:</p>
                <pre className="text-xs text-green-700 overflow-x-auto">{generatedTargetJson}</pre>
              </div>
            )}
            <p className="mt-2 text-xs text-gray-500">
              💡 Tip: Provide a complete example of how you want your logs structured. Include all fields you want to extract or transform.
            </p>
          </div>
        )}

        {/* AI Prompt Mode */}
        {targetMode === 'ai_prompt' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Prompt <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500 mb-2">
              Describe in natural language what structure you want for your transformed logs. AI will generate the target JSON structure based on your description and sample logs.
            </p>
            <textarea
              value={aiPrompt}
              onChange={(e) => setAiPrompt(e.target.value)}
              rows={6}
              className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm"
              placeholder='Example: "I want to extract the HTTP method, path, status code, and timestamp from the logs. Also include the client IP address and user agent. Format the timestamp as ISO 8601."'
              required
            />
            <div className="mt-3 flex items-center space-x-3">
              <button
                onClick={handleGenerateTargetJson}
                disabled={isGeneratingTarget || !aiPrompt.trim() || !customLogs.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 border border-transparent rounded-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingTarget ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Generating...
                  </span>
                ) : (
                  '🤖 Generate Target JSON from Prompt'
                )}
              </button>
              {generatedTargetJson && (
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    setTargetJson(generatedTargetJson)
                    setTargetMode('json')
                  }}
                  type="button"
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  style={{ cursor: 'pointer' }}
                >
                  Use Generated JSON
                </button>
              )}
            </div>
            {generatedTargetJson && (
              <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-xs text-blue-800 font-medium mb-2">Generated Target JSON:</p>
                <pre className="text-xs text-blue-700 bg-white p-2 rounded border border-blue-100 overflow-x-auto">{generatedTargetJson}</pre>
              </div>
            )}
            <p className="mt-2 text-xs text-gray-500">
              💡 Tip: Be specific about the fields you want. Mention data types, formats, and any transformations needed (e.g., "convert timestamp to ISO 8601", "extract IP address", "parse status code as integer").
            </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mb-6">
        {/* Debug info - show why buttons are disabled */}
        {(transformMutation.isPending || !customLogs.trim() || (targetMode === 'json' && !targetJson.trim()) || (targetMode === 'ai_prompt' && !aiPrompt.trim())) && (
          <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800 font-medium mb-1">⚠️ Button Requirements:</p>
            <ul className="text-xs text-yellow-700 list-disc list-inside space-y-1">
              {!customLogs.trim() && <li>Sample logs are required</li>}
              {targetMode === 'json' && !targetJson.trim() && <li>Target JSON is required</li>}
              {targetMode === 'ai_prompt' && !aiPrompt.trim() && <li>AI prompt is required</li>}
              {transformMutation.isPending && <li>Generation in progress...</li>}
            </ul>
          </div>
        )}
        <div className="flex justify-center space-x-4">
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              console.log('Generate button clicked', {
                customLogs: customLogs.trim().length,
                targetMode,
                targetJson: targetJson.trim().length,
                aiPrompt: aiPrompt.trim().length,
                isPending: transformMutation.isPending
              })
              handleGenerate()
            }}
            disabled={
              transformMutation.isPending || 
              !customLogs.trim() || 
              (targetMode === 'json' && !targetJson.trim()) ||
              (targetMode === 'ai_prompt' && !aiPrompt.trim())
            }
            type="button"
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            style={{ cursor: transformMutation.isPending || !customLogs.trim() || (targetMode === 'json' && !targetJson.trim()) || (targetMode === 'ai_prompt' && !aiPrompt.trim()) ? 'not-allowed' : 'pointer' }}
          >
          {transformMutation.isPending ? (
            <span className="flex items-center">
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing with AI...
            </span>
          ) : (
            '🤖 Generate Config with AI'
          )}
        </button>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            handleValidate()
          }}
          disabled={!generatedConfig || isValidating}
          type="button"
          className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium cursor-pointer"
        >
          {isValidating ? 'Validating...' : 'Validate Config'}
        </button>
        <button
          onClick={(e) => {
            e.preventDefault()
            e.stopPropagation()
            console.log('Dry Run button clicked', { generatedConfig: !!generatedConfig, customLogs: !!customLogs, isValidating })
            handleDryRun()
          }}
          disabled={!generatedConfig || !customLogs || isValidating}
          type="button"
          className="bg-purple-600 text-white px-6 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          style={{ cursor: !generatedConfig || !customLogs || isValidating ? 'not-allowed' : 'pointer' }}
        >
          {isValidating ? 'Running...' : 'Dry Run'}
        </button>
        </div>
        {(!generatedConfig || !customLogs) && (
          <div className="mt-3 p-2 bg-gray-50 border border-gray-200 rounded-md">
            <p className="text-xs text-gray-600">
              💡 <strong>Validate Config</strong> and <strong>Dry Run</strong> will be enabled after generating a config.
            </p>
          </div>
        )}
      </div>

      {/* Generated Config */}
      {generatedConfig && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Generated OTel Config</h2>
            <button
              onClick={() => {
                navigator.clipboard.writeText(generatedConfig)
                alert('Config copied to clipboard!')
              }}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              📋 Copy
            </button>
          </div>
          <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-sm border border-gray-200">
            <code>{generatedConfig}</code>
          </pre>
        </div>
      )}

      {/* Validation/Dry Run Result */}
      {validationResult && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">
            {validationResult.transformed_logs ? 'Dry Run Result' : 'Generation Result'}
          </h2>
          <div className={`p-4 rounded-md ${validationResult.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <p className={`font-semibold ${validationResult.valid ? 'text-green-800' : 'text-red-800'}`}>
              {validationResult.valid ? '✓ Configuration Generated' : '✗ Configuration Generation Failed'}
            </p>
            {validationResult.transformed_logs && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 mb-2">Transformed Logs:</p>
                <pre className="bg-white p-3 rounded border border-gray-200 overflow-x-auto text-xs">
                  {JSON.stringify(validationResult.transformed_logs, null, 2)}
                </pre>
              </div>
            )}
            {validationResult.warnings && validationResult.warnings.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium text-yellow-800 mb-1">⚠️ Warnings:</p>
                <ul className="list-disc list-inside text-yellow-700 text-sm space-y-1">
                  {validationResult.warnings.map((warning: string, idx: number) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}
            {validationResult.errors && validationResult.errors.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium text-red-800 mb-1">❌ Errors:</p>
                <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                  {validationResult.errors.map((error: string, idx: number) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}


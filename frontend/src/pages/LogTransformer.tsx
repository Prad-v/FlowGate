import { useState } from 'react'
import { templateApi } from '../services/api'

export default function LogTransformer() {
  const [sampleLogs, setSampleLogs] = useState('')
  const [targetJson, setTargetJson] = useState('')
  const [generatedConfig, setGeneratedConfig] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  const handleGenerate = () => {
    // Placeholder for AI generation
    // In production, this would call an AI service
    const placeholderConfig = `processors:
  transform:
    log_statements:
      - context: log
        statements:
          - set(attributes["level"], "INFO") where body matches "INFO"
          - set(attributes["level"], "ERROR") where body matches "ERROR"
          - extract(attributes["order_id"], "Order (\\d+)") where body matches "Order"
          - extract(attributes["customer"], "customer ([A-Z0-9]+)") where body matches "customer"
`
    setGeneratedConfig(placeholderConfig)
  }

  const handleValidate = async () => {
    if (!generatedConfig) return
    setIsValidating(true)
    try {
      const result = await templateApi.validate(generatedConfig)
      setValidationResult(result)
    } catch (error) {
      setValidationResult({ valid: false, errors: ['Validation failed'] })
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Log Transformer Studio</h1>
        <p className="mt-2 text-sm text-gray-600">
          Transform unstructured logs into structured JSON using AI-assisted OTel config generation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Sample Logs (Input)</h2>
          <textarea
            value={sampleLogs}
            onChange={(e) => setSampleLogs(e.target.value)}
            rows={15}
            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm"
            placeholder="INFO 2024-01-02 Order 54321 processed for customer AB12&#10;ERROR 2024-01-02 Order 54322 failed for customer CD34"
          />
        </div>

        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Target Structured JSON</h2>
          <textarea
            value={targetJson}
            onChange={(e) => setTargetJson(e.target.value)}
            rows={15}
            className="w-full border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500 font-mono text-sm"
            placeholder='{"level": "INFO", "order_id": 54321, "customer": "AB12"}'
          />
        </div>
      </div>

      <div className="mb-6 flex justify-center space-x-4">
        <button
          onClick={handleGenerate}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
        >
          Generate Config
        </button>
        <button
          onClick={handleValidate}
          disabled={!generatedConfig || isValidating}
          className="bg-green-600 text-white px-6 py-2 rounded-md hover:bg-green-700 disabled:opacity-50"
        >
          {isValidating ? 'Validating...' : 'Dry Run'}
        </button>
      </div>

      {generatedConfig && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Generated OTel Config</h2>
          <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-sm">
            <code>{generatedConfig}</code>
          </pre>
        </div>
      )}

      {validationResult && (
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Validation Result</h2>
          <div className={`p-4 rounded-md ${validationResult.valid ? 'bg-green-50' : 'bg-red-50'}`}>
            <p className={`font-semibold ${validationResult.valid ? 'text-green-800' : 'text-red-800'}`}>
              {validationResult.valid ? '✓ Valid Configuration' : '✗ Invalid Configuration'}
            </p>
            {validationResult.errors && validationResult.errors.length > 0 && (
              <ul className="mt-2 list-disc list-inside text-red-800">
                {validationResult.errors.map((error: string, idx: number) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            )}
            {validationResult.warnings && validationResult.warnings.length > 0 && (
              <ul className="mt-2 list-disc list-inside text-yellow-800">
                {validationResult.warnings.map((warning: string, idx: number) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

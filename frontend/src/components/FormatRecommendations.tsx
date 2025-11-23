import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { logTransformationApi, FormatRecommendation, FormatRecommendationRequest } from '../services/api'

interface FormatRecommendationsProps {
  sourceFormat?: string | null
  sampleLogs?: string
  onSelectFormat: (formatName: string) => void
}

export default function FormatRecommendations({
  sourceFormat,
  sampleLogs,
  onSelectFormat,
}: FormatRecommendationsProps) {
  const [useCase, setUseCase] = useState<string>('')

  const recommendationMutation = useMutation({
    mutationFn: (request: FormatRecommendationRequest) =>
      logTransformationApi.getRecommendations(request),
  })

  const handleGetRecommendations = () => {
    recommendationMutation.mutate({
      source_format: sourceFormat || null,
      sample_logs: sampleLogs || null,
      use_case: useCase || null,
    })
  }

  const recommendations = recommendationMutation.data?.recommendations || []

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">AI Format Recommendations</h3>
        <button
          onClick={handleGetRecommendations}
          disabled={recommendationMutation.isPending}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {recommendationMutation.isPending ? 'Getting Recommendations...' : 'Get Recommendations'}
        </button>
      </div>

      {useCase && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Use Case (Optional)</label>
          <input
            type="text"
            value={useCase}
            onChange={(e) => setUseCase(e.target.value)}
            placeholder="e.g., monitoring, analytics, compliance"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      )}

      {recommendationMutation.isError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm font-medium text-red-800 mb-1">Error getting recommendations</p>
          <p className="text-xs text-red-700">
            {recommendationMutation.error instanceof Error
              ? recommendationMutation.error.message
              : (recommendationMutation.error as any)?.response?.data?.detail || 
                (recommendationMutation.error as any)?.message || 
                'Network Error - Please check your connection and try again'}
          </p>
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-600">
            {recommendationMutation.data?.message || 'Recommended destination formats:'}
          </p>
          {recommendations.map((rec: FormatRecommendation, idx: number) => (
            <div
              key={idx}
              className="p-4 border border-gray-200 rounded-md hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer"
              onClick={() => onSelectFormat(rec.format_name)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium text-gray-900">{rec.display_name}</h4>
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                      {Math.round(rec.confidence_score * 100)}% confidence
                    </span>
                    {rec.compatibility_score && (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        {Math.round(rec.compatibility_score * 100)}% compatible
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">{rec.reasoning}</p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onSelectFormat(rec.format_name)
                  }}
                  className="ml-4 px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100"
                >
                  Select
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {recommendations.length === 0 && !recommendationMutation.isPending && !recommendationMutation.isError && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">Click "Get Recommendations" to see AI-suggested destination formats</p>
        </div>
      )}
    </div>
  )
}


import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { logTransformationApi, LogFormatTemplate } from '../services/api'

interface LogFormatSelectorProps {
  value?: string | null
  onChange: (formatName: string | null) => void
  formatType?: 'source' | 'destination' | 'both'
  label: string
  placeholder?: string
  showPreview?: boolean
}

export default function LogFormatSelector({
  value,
  onChange,
  formatType,
  label,
  placeholder = 'Select a format...',
  showPreview = true,
}: LogFormatSelectorProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<LogFormatTemplate | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['log-formats', formatType],
    queryFn: () => logTransformationApi.getFormats(formatType),
  })

  useEffect(() => {
    if (value && data) {
      const template = data.templates.find((t) => t.format_name === value)
      setSelectedTemplate(template || null)
    } else {
      setSelectedTemplate(null)
    }
  }, [value, data])

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const formatName = e.target.value || null
    onChange(formatName)
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <select
        value={value || ''}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
        disabled={isLoading}
      >
        <option value="">{placeholder}</option>
        {data?.templates.map((template) => (
          <option key={template.id} value={template.format_name}>
            {template.display_name}
          </option>
        ))}
      </select>

      {showPreview && selectedTemplate && (
        <div className="mt-3 p-3 bg-gray-50 border border-gray-200 rounded-md">
          <div className="text-xs font-medium text-gray-700 mb-2">Format Preview</div>
          {selectedTemplate.description && (
            <p className="text-xs text-gray-600 mb-2">{selectedTemplate.description}</p>
          )}
          {selectedTemplate.sample_logs && (
            <div className="mt-2">
              <div className="text-xs font-medium text-gray-700 mb-1">Sample Logs:</div>
              <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                {selectedTemplate.sample_logs}
              </pre>
            </div>
          )}
          {selectedTemplate.schema && (
            <div className="mt-2">
              <div className="text-xs font-medium text-gray-700 mb-1">Expected Schema:</div>
              <pre className="text-xs bg-white p-2 rounded border border-gray-200 overflow-x-auto">
                {JSON.stringify(selectedTemplate.schema, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}


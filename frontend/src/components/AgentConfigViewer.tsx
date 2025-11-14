import React, { useState } from 'react'
import { AgentConfig } from '../services/api'

interface AgentConfigViewerProps {
  config: AgentConfig
}

export default function AgentConfigViewer({ config }: AgentConfigViewerProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(config.config_yaml)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([config.config_yaml], { type: 'text/yaml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `gateway-config-v${config.config_version || 'latest'}.yaml`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Configuration</h3>
          {config.config_version && (
            <p className="text-sm text-gray-500">Version: {config.config_version}</p>
          )}
          {config.last_updated && (
            <p className="text-sm text-gray-500">
              Last updated: {new Date(config.last_updated).toLocaleString()}
            </p>
          )}
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Download
          </button>
        </div>
      </div>
      <div className="bg-gray-900 rounded-lg p-4 overflow-auto max-h-96">
        <pre className="text-sm text-gray-100 font-mono whitespace-pre-wrap">
          {config.config_yaml}
        </pre>
      </div>
    </div>
  )
}


import React, { useState, useMemo } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface ConfigDiffViewerProps {
  agentConfig: string
  standardConfig: string
  diff: string
  diffStats?: {
    added: number
    removed: number
    modified: number
    total_agent_lines: number
    total_standard_lines: number
    similarity_ratio: number
  }
  viewMode?: 'unified' | 'side-by-side'
}

export default function ConfigDiffViewer({
  agentConfig,
  standardConfig,
  diff,
  diffStats,
  viewMode: initialViewMode = 'unified',
}: ConfigDiffViewerProps) {
  const [viewMode, setViewMode] = useState<'unified' | 'side-by-side'>(initialViewMode)

  // Parse diff lines for unified view
  const diffLines = useMemo(() => {
    return diff.split('\n').map((line, index) => {
      let type: 'added' | 'removed' | 'context' | 'header' = 'context'
      let content = line

      if (line.startsWith('+++') || line.startsWith('---')) {
        type = 'header'
      } else if (line.startsWith('+') && !line.startsWith('+++')) {
        type = 'added'
        content = line.substring(1)
      } else if (line.startsWith('-') && !line.startsWith('---')) {
        type = 'removed'
        content = line.substring(1)
      }

      return { type, content, lineNumber: index + 1 }
    })
  }, [diff])

  // Parse configs for side-by-side view
  const agentLines = useMemo(() => agentConfig.split('\n'), [agentConfig])
  const standardLines = useMemo(() => standardConfig.split('\n'), [standardConfig])

  // Create side-by-side diff mapping
  const sideBySideDiff = useMemo(() => {
    const result: Array<{
      agentLine: string | null
      standardLine: string | null
      agentType: 'added' | 'removed' | 'modified' | 'unchanged' | null
      standardType: 'added' | 'removed' | 'modified' | 'unchanged' | null
      agentLineNum: number | null
      standardLineNum: number | null
    }> = []

    // Simple line-by-line comparison
    const maxLines = Math.max(agentLines.length, standardLines.length)
    let agentIdx = 0
    let standardIdx = 0

    for (let i = 0; i < maxLines; i++) {
      const agentLine = agentIdx < agentLines.length ? agentLines[agentIdx] : null
      const standardLine = standardIdx < standardLines.length ? standardLines[standardIdx] : null

      if (agentLine === standardLine) {
        // Lines match
        result.push({
          agentLine,
          standardLine,
          agentType: 'unchanged',
          standardType: 'unchanged',
          agentLineNum: agentIdx + 1,
          standardLineNum: standardIdx + 1,
        })
        agentIdx++
        standardIdx++
      } else if (agentLine && !standardLine) {
        // Line added in agent
        result.push({
          agentLine,
          standardLine: null,
          agentType: 'added',
          standardType: null,
          agentLineNum: agentIdx + 1,
          standardLineNum: null,
        })
        agentIdx++
      } else if (!agentLine && standardLine) {
        // Line removed from standard
        result.push({
          agentLine: null,
          standardLine,
          agentType: null,
          standardType: 'removed',
          agentLineNum: null,
          standardLineNum: standardIdx + 1,
        })
        standardIdx++
      } else {
        // Lines differ (modified)
        result.push({
          agentLine,
          standardLine,
          agentType: 'modified',
          standardType: 'modified',
          agentLineNum: agentIdx + 1,
          standardLineNum: standardIdx + 1,
        })
        agentIdx++
        standardIdx++
      }
    }

    return result
  }, [agentLines, standardLines])

  const getLineClassName = (type: string) => {
    switch (type) {
      case 'added':
        return 'bg-green-900/30 border-l-2 border-green-500'
      case 'removed':
        return 'bg-red-900/30 border-l-2 border-red-500'
      case 'modified':
        return 'bg-yellow-900/30 border-l-2 border-yellow-500'
      case 'header':
        return 'bg-gray-800 text-gray-400'
      default:
        return ''
    }
  }

  return (
    <div className="space-y-4">
      {/* Header with stats and view toggle */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {diffStats && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-600">Stats:</span>
              <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                +{diffStats.added}
              </span>
              <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">
                -{diffStats.removed}
              </span>
              {diffStats.modified > 0 && (
                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">
                  ~{diffStats.modified}
                </span>
              )}
              <span className="text-gray-500 text-xs">
                Similarity: {(diffStats.similarity_ratio * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewMode('unified')}
            className={`px-3 py-1.5 text-sm rounded-md ${
              viewMode === 'unified'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Unified
          </button>
          <button
            onClick={() => setViewMode('side-by-side')}
            className={`px-3 py-1.5 text-sm rounded-md ${
              viewMode === 'side-by-side'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Side-by-Side
          </button>
        </div>
      </div>

      {/* Diff content */}
      <div className="border rounded-lg overflow-hidden">
        {viewMode === 'unified' ? (
          <div className="bg-gray-900">
            <div className="overflow-auto max-h-96">
              <pre className="text-sm">
                {diffLines.map((line, idx) => (
                  <div
                    key={idx}
                    className={`px-4 py-0.5 ${getLineClassName(line.type)} ${
                      line.type === 'header' ? 'text-gray-400' : 'text-gray-100'
                    }`}
                  >
                    <span className="inline-block w-12 text-gray-500 text-right mr-4">
                      {line.type !== 'header' && line.lineNumber}
                    </span>
                    <span className="inline-block w-4 mr-2">
                      {line.type === 'added' && '+'}
                      {line.type === 'removed' && '-'}
                      {line.type === 'context' && ' '}
                    </span>
                    <span>{line.content}</span>
                  </div>
                ))}
              </pre>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 divide-x divide-gray-700 bg-gray-900">
            {/* Standard Config */}
            <div className="overflow-auto max-h-96">
              <div className="bg-gray-800 px-2 py-1 text-xs text-gray-400 border-b border-gray-700">
                Standard Config
              </div>
              <div className="overflow-auto">
                <SyntaxHighlighter
                  language="yaml"
                  style={vscDarkPlus}
                  customStyle={{ margin: 0, padding: '0.5rem' }}
                  showLineNumbers
                >
                  {standardConfig}
                </SyntaxHighlighter>
              </div>
            </div>

            {/* Agent Config */}
            <div className="overflow-auto max-h-96">
              <div className="bg-gray-800 px-2 py-1 text-xs text-gray-400 border-b border-gray-700">
                Agent Config
              </div>
              <div className="overflow-auto">
                <SyntaxHighlighter
                  language="yaml"
                  style={vscDarkPlus}
                  customStyle={{ margin: 0, padding: '0.5rem' }}
                  showLineNumbers
                >
                  {agentConfig}
                </SyntaxHighlighter>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 text-xs text-gray-600">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-green-500 border border-green-600"></div>
          <span>Added</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-red-500 border border-red-600"></div>
          <span>Removed</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-yellow-500 border border-yellow-600"></div>
          <span>Modified</span>
        </div>
      </div>
    </div>
  )
}


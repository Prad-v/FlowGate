import React, { useState, useMemo, useCallback, useEffect } from 'react'
import { AvailableComponents, AvailableComponent } from '../services/api'
import ReactFlow, { Node, Edge, Background, Controls, MiniMap, useNodesState, useEdgesState, ConnectionMode } from 'reactflow'
import 'reactflow/dist/style.css'

interface AvailableComponentsDisplayProps {
  availableComponents?: AvailableComponents
  onRefresh?: () => void
  isLoading?: boolean
}

type ViewMode = 'table' | 'graph'

function getComponentTypeColor(type: string) {
  switch (type) {
    case 'receiver':
      return 'bg-blue-100 text-blue-800 border-blue-300'
    case 'processor':
      return 'bg-green-100 text-green-800 border-green-300'
    case 'exporter':
      return 'bg-orange-100 text-orange-800 border-orange-300'
    case 'extension':
      return 'bg-purple-100 text-purple-800 border-purple-300'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300'
  }
}

function getStabilityBadgeColor(stability?: string) {
  switch (stability) {
    case 'stable':
      return 'bg-green-100 text-green-800'
    case 'experimental':
      return 'bg-yellow-100 text-yellow-800'
    case 'deprecated':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function ComponentRow({ component, level = 0 }: { component: AvailableComponent; level?: number }) {
  const [expanded, setExpanded] = useState(false)
  const hasSubComponents = component.sub_components && component.sub_components.length > 0

  return (
    <>
      <tr className={level > 0 ? 'bg-gray-50' : ''}>
        <td className="px-4 py-3 whitespace-nowrap text-sm" style={{ paddingLeft: `${16 + level * 24}px` }}>
          {hasSubComponents && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mr-2 text-gray-500 hover:text-gray-700"
            >
              {expanded ? '▼' : '▶'}
            </button>
          )}
          <span className="font-medium text-gray-900">{component.name}</span>
          <span className="ml-2 text-xs text-gray-500">({component.component_id})</span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getComponentTypeColor(component.component_type)}`}>
            {component.component_type}
          </span>
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
          {component.version || 'N/A'}
        </td>
        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
          {component.supported_data_types && component.supported_data_types.length > 0 ? (
            <div className="flex gap-1">
              {component.supported_data_types.map((type) => (
                <span key={type} className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                  {type}
                </span>
              ))}
            </div>
          ) : (
            'N/A'
          )}
        </td>
        <td className="px-4 py-3 whitespace-nowrap">
          {component.stability ? (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStabilityBadgeColor(component.stability)}`}>
              {component.stability}
            </span>
          ) : (
            <span className="text-sm text-gray-400">N/A</span>
          )}
        </td>
      </tr>
      {expanded && hasSubComponents && component.sub_components?.map((sub) => (
        <ComponentRow key={sub.component_id} component={sub} level={level + 1} />
      ))}
    </>
  )
}

function TableView({ components, filterType, searchTerm }: { components: AvailableComponent[]; filterType: string; searchTerm: string }) {
  const filteredComponents = useMemo(() => {
    let filtered = components

    if (filterType && filterType !== 'all') {
      filtered = filtered.filter((c) => c.component_type === filterType)
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(
        (c) =>
          c.name.toLowerCase().includes(term) ||
          c.component_id.toLowerCase().includes(term) ||
          (c.version && c.version.toLowerCase().includes(term))
      )
    }

    return filtered
  }, [components, filterType, searchTerm])

  if (filteredComponents.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No components found matching the current filters.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Component Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Version
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Data Types
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Stability
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredComponents.map((component) => (
            <ComponentRow key={component.component_id} component={component} />
          ))}
        </tbody>
      </table>
    </div>
  )
}

function GraphView({ components }: { components: AvailableComponent[] }) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  const toggleNode = useCallback((nodeId: string) => {
    setExpandedNodes((prev) => {
      const next = new Set(prev)
      if (next.has(nodeId)) {
        next.delete(nodeId)
      } else {
        next.add(nodeId)
      }
      return next
    })
  }, [])

  const { nodes: computedNodes, edges: computedEdges } = useMemo(() => {
    const graphNodes: Node[] = []
    const graphEdges: Edge[] = []
    const nodePositions = new Map<string, { x: number; y: number }>()

    // Group components by type for better layout
    const componentsByType: Record<string, AvailableComponent[]> = {
      receiver: [],
      processor: [],
      exporter: [],
      extension: [],
      unknown: [],
    }

    components.forEach((comp) => {
      const type = comp.component_type || 'unknown'
      if (!componentsByType[type]) {
        componentsByType[type] = []
      }
      componentsByType[type].push(comp)
    })

    // Calculate positions
    let yOffset = 0
    const xSpacing = 300
    const ySpacing = 100

    Object.entries(componentsByType).forEach(([type, typeComponents], typeIndex) => {
      if (typeComponents.length === 0) return

      const xPos = typeIndex * xSpacing + 100
      let currentY = yOffset

      typeComponents.forEach((comp, index) => {
        const nodeId = comp.component_id
        const yPos = currentY + index * ySpacing

        nodePositions.set(nodeId, { x: xPos, y: yPos })

        const bgColor = type === 'receiver' ? '#dbeafe' : type === 'processor' ? '#dcfce7' : type === 'exporter' ? '#fed7aa' : type === 'extension' ? '#e9d5ff' : '#f3f4f6'
        const textColor = type === 'receiver' ? '#1e40af' : type === 'processor' ? '#166534' : type === 'exporter' ? '#9a3412' : type === 'extension' ? '#6b21a8' : '#374151'

        graphNodes.push({
          id: nodeId,
          type: 'default',
          position: { x: xPos, y: yPos },
          data: {
            label: (
              <div className="px-3 py-2">
                <div className="font-semibold text-sm" style={{ color: textColor }}>
                  {comp.name}
                </div>
                <div className="text-xs text-gray-500 mt-1">{comp.component_type}</div>
                {comp.version && <div className="text-xs text-gray-400 mt-1">v{comp.version}</div>}
                {comp.sub_components && comp.sub_components.length > 0 && (
                  <div className="mt-2 text-xs text-blue-600">
                    {expandedNodes.has(nodeId) ? '▼' : '▶'} {comp.sub_components.length} sub-components
                  </div>
                )}
              </div>
            ),
            component: comp,
          },
          style: {
            background: bgColor,
            border: `2px solid ${textColor}`,
            borderRadius: '8px',
            width: 200,
            minHeight: 100,
          },
        })

        // Add edges for sub-components if expanded
        if (expandedNodes.has(nodeId) && comp.sub_components) {
          comp.sub_components.forEach((subComp, subIndex) => {
            const subNodeId = `${nodeId}_${subComp.component_id}`
            const subXPos = xPos + 250
            const subYPos = yPos + subIndex * 80

            graphNodes.push({
              id: subNodeId,
              type: 'default',
              position: { x: subXPos, y: subYPos },
              data: {
                label: (
                  <div className="px-2 py-1">
                    <div className="font-medium text-xs">{subComp.name}</div>
                    <div className="text-xs text-gray-400">{subComp.component_type}</div>
                  </div>
                ),
                component: subComp,
              },
              style: {
                background: '#f9fafb',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                width: 150,
              },
            })

            graphEdges.push({
              id: `${nodeId}-${subNodeId}`,
              source: nodeId,
              target: subNodeId,
              type: 'smoothstep',
              animated: true,
            })
          })
        }
      })

      yOffset = Math.max(yOffset, currentY + typeComponents.length * ySpacing)
    })

    return { nodes: graphNodes, edges: graphEdges }
  }, [components, expandedNodes])

  const [nodesState, setNodes, onNodesChange] = useNodesState(computedNodes)
  const [edgesState, setEdges, onEdgesChange] = useEdgesState(computedEdges)

  // Update nodes and edges when they change
  useEffect(() => {
    setNodes(computedNodes)
    setEdges(computedEdges)
  }, [computedNodes, computedEdges, setNodes, setEdges])

  return (
    <div style={{ width: '100%', height: '600px', border: '1px solid #e5e7eb', borderRadius: '8px' }}>
      <ReactFlow
        nodes={nodesState}
        edges={edgesState}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionMode={ConnectionMode.Loose}
        fitView
        onNodeClick={(event, node) => {
          const component = node.data?.component as AvailableComponent | undefined
          if (component?.sub_components && component.sub_components.length > 0) {
            toggleNode(node.id)
          }
        }}
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}

export default function AvailableComponentsDisplay({
  availableComponents,
  onRefresh,
  isLoading = false,
}: AvailableComponentsDisplayProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [filterType, setFilterType] = useState<string>('all')
  const [searchTerm, setSearchTerm] = useState<string>('')

  const components = availableComponents?.components || []

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        <p className="mt-2 text-sm text-gray-500">Loading available components...</p>
      </div>
    )
  }

  if (!availableComponents || components.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-gray-500 mb-4">
          No available components data. The agent may not support ReportsAvailableComponents capability.
        </p>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
          >
            Request Available Components
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-4">
          <div className="flex rounded-md shadow-sm" role="group">
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-2 text-sm font-medium rounded-l-md border ${
                viewMode === 'table'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Table View
            </button>
            <button
              onClick={() => setViewMode('graph')}
              className={`px-4 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                viewMode === 'graph'
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              Graph View
            </button>
          </div>
        </div>

        <div className="flex items-center gap-4 flex-1 sm:flex-initial sm:justify-end">
          {viewMode === 'table' && (
            <>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="receiver">Receivers</option>
                <option value="processor">Processors</option>
                <option value="exporter">Exporters</option>
                <option value="extension">Extensions</option>
              </select>

              <input
                type="text"
                placeholder="Search components..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[200px]"
              />
            </>
          )}

          {onRefresh && (
            <button
              onClick={onRefresh}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 text-sm font-medium"
            >
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Component count and info */}
      <div className="text-sm text-gray-600">
        Showing {components.length} component{components.length !== 1 ? 's' : ''}
        {availableComponents.hash && (
          <span className="ml-4 text-xs text-gray-400">Hash: {availableComponents.hash}</span>
        )}
        {availableComponents.last_updated && (
          <span className="ml-4 text-xs text-gray-400">
            Last updated: {new Date(availableComponents.last_updated).toLocaleString()}
          </span>
        )}
      </div>

      {/* View content */}
      {viewMode === 'table' ? (
        <TableView components={components} filterType={filterType} searchTerm={searchTerm} />
      ) : (
        <GraphView components={components} />
      )}
    </div>
  )
}


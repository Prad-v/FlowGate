import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  addEdge,
  MarkerType,
  NodeTypes,
  EdgeTypes,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { otelBuilderApi, ComponentMetadata, BuilderNode, BuilderEdge, BuilderGenerateResponse } from '../services/api'
import { useQuery, useMutation } from '@tanstack/react-query'
import ComponentConfigForm from './ComponentConfigForm'

interface OtelBuilderProps {
  onSave?: (yaml: string, graph: { nodes: BuilderNode[]; edges: BuilderEdge[] }, metadata: { name: string; description?: string; templateType: string }) => void
  initialGraph?: { nodes: BuilderNode[]; edges: BuilderEdge[] }
}

const COMPONENT_COLORS = {
  receiver: { bg: '#dbeafe', border: '#3b82f6', text: '#1e40af' },
  processor: { bg: '#dcfce7', border: '#22c55e', text: '#166534' },
  exporter: { bg: '#fed7aa', border: '#f97316', text: '#9a3412' },
  connector: { bg: '#e9d5ff', border: '#a855f7', text: '#6b21a8' },
  extension: { bg: '#fce7f3', border: '#ec4899', text: '#9f1239' },
  pipeline: { bg: '#f3f4f6', border: '#6b7280', text: '#374151' },
}

const COMPONENT_ICONS = {
  receiver: '📥',
  processor: '⚙️',
  exporter: '📤',
  connector: '🔗',
  extension: '🔌',
  pipeline: '🔄',
}

function OtelBuilderInner({ onSave, initialGraph }: OtelBuilderProps) {
  const [selectedComponentType, setSelectedComponentType] = useState<'receiver' | 'processor' | 'exporter' | 'connector' | 'extension' | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [source, setSource] = useState<'static' | 'live'>('static')
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [yamlPreview, setYamlPreview] = useState<string>('')
  const [warnings, setWarnings] = useState<string[]>([])
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [templateName, setTemplateName] = useState('')
  const [templateDescription, setTemplateDescription] = useState('')
  const [templateType, setTemplateType] = useState<'metrics' | 'logs' | 'traces' | 'routing' | 'composite'>('composite')
  const [showExportModal, setShowExportModal] = useState(false)
  const [exportJson, setExportJson] = useState<string>('')

  // Load components
  const { data: componentsData, isLoading: componentsLoading, error: componentsError } = useQuery({
    queryKey: ['otel-components', selectedComponentType, source, searchTerm],
    queryFn: () => otelBuilderApi.getComponents(selectedComponentType || undefined, source, searchTerm || undefined),
  })

  // Log for debugging
  useEffect(() => {
    if (componentsData) {
      console.log('Components data received:', componentsData)
      console.log('Component types:', Object.keys(componentsData))
      Object.entries(componentsData).forEach(([type, components]: [string, any]) => {
        console.log(`${type}: ${components?.length || 0} components`)
      })
    }
    if (componentsError) {
      console.error('Error loading components:', componentsError)
    }
  }, [componentsData, componentsError])

  // Initialize nodes and edges
  const initialNodes: Node[] = useMemo(() => {
    if (initialGraph?.nodes) {
      return initialGraph.nodes
        .filter((n) => n.component_id && n.type) // Filter out invalid nodes
        .map((n) => ({
          id: n.id,
          type: 'default',
          position: n.position || { x: 0, y: 0 },
          data: {
            label: n.label || n.component_id,
            componentType: n.type,
            componentId: n.component_id,
            config: n.config || {},
            pipelineType: n.pipeline_type,
          },
          style: {
            background: COMPONENT_COLORS[n.type]?.bg || '#f3f4f6',
            border: `2px solid ${COMPONENT_COLORS[n.type]?.border || '#6b7280'}`,
            borderRadius: '8px',
            width: 180,
            minHeight: 80,
            color: COMPONENT_COLORS[n.type]?.text || '#374151',
          },
        }))
    }
    return []
  }, [initialGraph])

  const initialEdges: Edge[] = useMemo(() => {
    if (initialGraph?.edges && initialGraph?.nodes) {
      // Create a set of valid node IDs for validation
      const validNodeIds = new Set(initialGraph.nodes.map(n => n.id))
      
      // Filter and map edges, ensuring source and target nodes exist
      const validEdges = initialGraph.edges
        .filter((e) => {
          const sourceExists = validNodeIds.has(e.source)
          const targetExists = validNodeIds.has(e.target)
          if (!sourceExists || !targetExists) {
            console.warn(`Edge ${e.id} has invalid source or target:`, {
              source: e.source,
              target: e.target,
              sourceExists,
              targetExists,
            })
            return false
          }
          return true
        })
        .map((e) => ({
          id: e.id,
          source: e.source,
          target: e.target,
          type: 'smoothstep',
          animated: true,
          markerEnd: { type: MarkerType.ArrowClosed },
        }))
      
      console.log('Initial edges loaded:', {
        total: initialGraph.edges.length,
        valid: validEdges.length,
        invalid: initialGraph.edges.length - validEdges.length,
      })
      
      return validEdges
    }
    return []
  }, [initialGraph])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Generate YAML when graph changes
  const generateYamlMutation = useMutation({
    mutationFn: (graph: { nodes: BuilderNode[]; edges: BuilderEdge[] }) => otelBuilderApi.generateConfig(graph),
    onSuccess: (data: BuilderGenerateResponse) => {
      setYamlPreview(data.yaml)
      setWarnings(data.warnings)
    },
    onError: (error: any) => {
      console.error('Failed to generate YAML:', error)
      setYamlPreview('')
      setWarnings([`Failed to generate YAML: ${error.response?.data?.detail || error.message}`])
    },
  })

  useEffect(() => {
    // Filter out nodes without required fields
    const builderNodes: BuilderNode[] = nodes
      .filter((n) => n.data?.componentType && n.data?.componentId)
      .map((n) => ({
        id: n.id,
        type: n.data.componentType as any,
        component_id: n.data.componentId,
        label: n.data.label,
        config: n.data.config || {},
        pipeline_type: n.data.pipelineType,
        position: n.position,
      }))

    const builderEdges: BuilderEdge[] = edges
      .filter((e) => e.source && e.target)
      .map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }))

    // Only generate YAML if we have valid nodes
    if (builderNodes.length > 0) {
      generateYamlMutation.mutate({ nodes: builderNodes, edges: builderEdges })
    } else {
      setYamlPreview('')
      setWarnings([])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, edges])

  const onConnect = useCallback(
    (params: any) => {
      const newEdge = {
        ...params,
        id: `edge-${params.source}-${params.target}`,
        type: 'smoothstep',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
      }
      setEdges((eds) => addEdge(newEdge, eds))
    },
    [setEdges]
  )

  const onDragStart = (event: React.DragEvent, component: ComponentMetadata) => {
    // Set drag data - this must be done in dragstart
    const componentJson = JSON.stringify(component)
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('application/reactflow', componentJson)
    // Also set as text/plain as fallback
    event.dataTransfer.setData('text/plain', componentJson)
    console.log('Drag started for component:', component.id, component.type)
  }

  const reactFlowWrapper = useRef<HTMLDivElement>(null)

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      event.stopPropagation()
      
      // Try to get data from multiple sources
      let componentData = event.dataTransfer.getData('application/reactflow')
      if (!componentData) {
        componentData = event.dataTransfer.getData('text/plain')
      }
      if (!componentData) {
        console.log('No component data in drop event. Available types:', event.dataTransfer.types)
        return
      }
      
      try {
        const component: ComponentMetadata = JSON.parse(componentData)
        console.log('Dropping component:', component.id, component.type)
        
        if (!reactFlowWrapper.current) {
          console.log('ReactFlow wrapper not available')
          return
        }
        
        const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect()
        
        // Calculate position relative to the flow canvas
        // Offset by half the node width/height to center on drop point
        const position = {
          x: Math.max(0, event.clientX - reactFlowBounds.left - 90),
          y: Math.max(0, event.clientY - reactFlowBounds.top - 40),
        }

        // Generate unique ID with timestamp and random component to allow multiple instances
        const uniqueId = `${component.type}-${component.id}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`

        const newNode: Node = {
          id: uniqueId,
          type: 'default',
          position,
          data: {
            label: component.name || component.id,
            componentType: component.type,
            componentId: component.id,
            config: component.default_config || {},
            componentMetadata: component, // Store full metadata for form
          },
          style: {
            background: COMPONENT_COLORS[component.type]?.bg || '#f3f4f6',
            border: `2px solid ${COMPONENT_COLORS[component.type]?.border || '#6b7280'}`,
            borderRadius: '8px',
            width: 180,
            minHeight: 80,
            color: COMPONENT_COLORS[component.type]?.text || '#374151',
          },
        }

        setNodes((nds) => {
          const newNodes = nds.concat(newNode)
          console.log('Added new node, total nodes:', newNodes.length)
          return newNodes
        })
      } catch (error) {
        console.error('Error parsing component data:', error)
      }
    },
    [setNodes]
  )

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.stopPropagation()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  const handleDeleteNode = useCallback(() => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id))
      setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id))
      setSelectedNode(null)
    }
  }, [selectedNode, setNodes, setEdges])

  const handleSave = useCallback(() => {
    if (onSave && yamlPreview && templateName) {
      const builderNodes: BuilderNode[] = nodes.map((n) => ({
        id: n.id,
        type: n.data.componentType as any,
        component_id: n.data.componentId,
        label: n.data.label,
        config: n.data.config || {},
        pipeline_type: n.data.pipelineType,
        position: n.position,
      }))

      const builderEdges: BuilderEdge[] = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
      }))

      onSave(yamlPreview, { nodes: builderNodes, edges: builderEdges }, {
        name: templateName,
        description: templateDescription,
        templateType: templateType,
      })
      setShowSaveModal(false)
      setTemplateName('')
      setTemplateDescription('')
      setTemplateType('composite')
    }
  }, [onSave, yamlPreview, nodes, edges, templateName, templateDescription, templateType])

  const filteredComponents = useMemo(() => {
    if (!componentsData) return {}
    return componentsData
  }, [componentsData])

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Component Palette */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Palette</h2>
          
          {/* Source Toggle */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Data Source</label>
            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setSource('static')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-l-md border ${
                  source === 'static'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Static
              </button>
              <button
                onClick={() => setSource('live')}
                className={`flex-1 px-3 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                  source === 'live'
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Live
              </button>
            </div>
          </div>

          {/* Search */}
          <input
            type="text"
            placeholder="Search components..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          {/* Component Type Filter */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Type</label>
            <select
              value={selectedComponentType || ''}
              onChange={(e) => setSelectedComponentType(e.target.value as any || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Types</option>
              <option value="receiver">Receivers</option>
              <option value="processor">Processors</option>
              <option value="exporter">Exporters</option>
              <option value="connector">Connectors</option>
              <option value="extension">Extensions</option>
            </select>
          </div>
        </div>

        {/* Component List */}
        <div className="flex-1 overflow-y-auto p-4">
          {componentsLoading ? (
            <div className="text-center py-8 text-gray-500">Loading components...</div>
          ) : componentsError ? (
            <div className="text-center py-8 text-red-500">
              Error loading components. Try switching to "Static" source.
            </div>
          ) : (
            <>
              {Object.entries(filteredComponents).map(([type, components]: [string, any]) => {
                const componentList = Array.isArray(components) ? components : []
                if (componentList.length === 0) return null
                return (
                  <div key={type} className="mb-6">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2 capitalize">{type}</h3>
                    <div className="space-y-2">
                      {componentList.map((comp: ComponentMetadata) => (
                        <div
                          key={comp.id}
                          draggable
                          onDragStart={(e) => onDragStart(e, comp)}
                          className="p-3 bg-gray-50 border border-gray-200 rounded-md cursor-move hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span>{COMPONENT_ICONS[comp.type] || '📦'}</span>
                                <span className="text-sm font-medium text-gray-900">{comp.name || comp.id}</span>
                              </div>
                              {comp.description && (
                                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{comp.description}</p>
                              )}
                            </div>
                          </div>
                          {comp.stability && (
                            <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-yellow-100 text-yellow-800 rounded">
                              {comp.stability}
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
              {Object.keys(filteredComponents).length === 0 || 
               Object.values(filteredComponents).every((comps: any) => !Array.isArray(comps) || comps.length === 0) ? (
                <div className="text-center py-8 text-gray-500">
                  {searchTerm ? 'No components match your search' : 'No components available. Try switching to "Live" source.'}
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>

      {/* Center - Canvas */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Builder Canvas</h2>
          <div className="flex gap-2">
            <button
              onClick={() => {
                const pipelineNode: Node = {
                  id: `pipeline-${Date.now()}`,
                  type: 'default',
                  position: { x: Math.random() * 400 + 200, y: Math.random() * 300 + 100 },
                  data: {
                    label: 'New Pipeline',
                    componentType: 'pipeline',
                    componentId: `pipeline-${Date.now()}`,
                    config: {},
                    pipelineType: undefined,
                  },
                  style: {
                    background: COMPONENT_COLORS.pipeline.bg,
                    border: `2px solid ${COMPONENT_COLORS.pipeline.border}`,
                    borderRadius: '8px',
                    width: 180,
                    minHeight: 80,
                    color: COMPONENT_COLORS.pipeline.text,
                  },
                }
                setNodes((nds) => nds.concat(pipelineNode))
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Add Pipeline
            </button>
            <label className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer">
              Import JSON
              <input
                type="file"
                accept=".json"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) {
                    const reader = new FileReader()
                    reader.onload = (event) => {
                      try {
                        const graph = JSON.parse(event.target?.result as string) as { nodes: BuilderNode[]; edges: BuilderEdge[] }
                        if (graph.nodes && graph.edges) {
                          const importedNodes: Node[] = graph.nodes.map((n) => ({
                            id: n.id,
                            type: 'default',
                            position: n.position || { x: 0, y: 0 },
                            data: {
                              label: n.label || n.component_id,
                              componentType: n.type,
                              componentId: n.component_id,
                              config: n.config || {},
                              pipelineType: n.pipeline_type,
                            },
                            style: {
                              background: COMPONENT_COLORS[n.type]?.bg || '#f3f4f6',
                              border: `2px solid ${COMPONENT_COLORS[n.type]?.border || '#6b7280'}`,
                              borderRadius: '8px',
                              width: 180,
                              minHeight: 80,
                              color: COMPONENT_COLORS[n.type]?.text || '#374151',
                            },
                          }))
                          const importedEdges: Edge[] = graph.edges.map((e) => ({
                            id: e.id,
                            source: e.source,
                            target: e.target,
                            type: 'smoothstep',
                            animated: true,
                            markerEnd: { type: MarkerType.ArrowClosed },
                          }))
                          setNodes(importedNodes)
                          setEdges(importedEdges)
                        }
                      } catch (error) {
                        alert('Failed to parse JSON file')
                      }
                    }
                    reader.readAsText(file)
                  }
                }}
              />
            </label>
            <button
              onClick={() => {
                const builderNodes: BuilderNode[] = nodes.map((n) => ({
                  id: n.id,
                  type: n.data.componentType as any,
                  component_id: n.data.componentId,
                  label: n.data.label,
                  config: n.data.config || {},
                  pipeline_type: n.data.pipelineType,
                  position: n.position,
                }))
                const builderEdges: BuilderEdge[] = edges.map((e) => ({
                  id: e.id,
                  source: e.source,
                  target: e.target,
                }))
                const graphJson = JSON.stringify({ nodes: builderNodes, edges: builderEdges }, null, 2)
                setExportJson(graphJson)
                setShowExportModal(true)
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Export JSON
            </button>
            <button
              onClick={() => {
                setNodes([])
                setEdges([])
                setSelectedNode(null)
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Clear
            </button>
            <button
              onClick={() => setShowSaveModal(true)}
              disabled={!yamlPreview}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Save as Template
            </button>
          </div>
        </div>
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            onDrop={onDrop}
            onDragOver={onDragOver}
            connectionMode={ConnectionMode.Loose}
            fitView
            deleteKeyCode={['Backspace', 'Delete']}
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
      </div>

      {/* Right Sidebar - YAML Preview & Node Config */}
      <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            {selectedNode ? 'Node Configuration' : 'YAML Preview'}
          </h2>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Component ID</label>
                <input
                  type="text"
                  value={selectedNode.data.componentId}
                  onChange={(e) => {
                    setNodes((nds) =>
                      nds.map((n) =>
                        n.id === selectedNode.id
                          ? { ...n, data: { ...n.data, componentId: e.target.value } }
                          : n
                      )
                    )
                    setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, componentId: e.target.value } })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Label</label>
                <input
                  type="text"
                  value={selectedNode.data.label}
                  onChange={(e) => {
                    setNodes((nds) =>
                      nds.map((n) =>
                        n.id === selectedNode.id ? { ...n, data: { ...n.data, label: e.target.value } } : n
                      )
                    )
                    setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, label: e.target.value } })
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>
              {selectedNode.data.componentType === 'pipeline' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Pipeline Type</label>
                  <select
                    value={selectedNode.data.pipelineType || ''}
                    onChange={(e) => {
                      setNodes((nds) =>
                        nds.map((n) =>
                          n.id === selectedNode.id
                            ? { ...n, data: { ...n.data, pipelineType: e.target.value } }
                            : n
                        )
                      )
                      setSelectedNode({
                        ...selectedNode,
                        data: { ...selectedNode.data, pipelineType: e.target.value },
                      })
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="">Select type...</option>
                    <option value="metrics">Metrics</option>
                    <option value="logs">Logs</option>
                    <option value="traces">Traces</option>
                  </select>
                </div>
              )}
              
              {/* Component Configuration Form */}
              {selectedNode.data.componentType !== 'pipeline' && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <ComponentConfigForm
                    componentId={selectedNode.data.componentId}
                    componentType={selectedNode.data.componentType}
                    config={selectedNode.data.config || {}}
                    defaultConfig={selectedNode.data.componentMetadata?.default_config || {}}
                    onChange={(newConfig) => {
                      setNodes((nds) =>
                        nds.map((n) =>
                          n.id === selectedNode.id ? { ...n, data: { ...n.data, config: newConfig } } : n
                        )
                      )
                      setSelectedNode({ ...selectedNode, data: { ...selectedNode.data, config: newConfig } })
                    }}
                  />
                </div>
              )}
              
              <div className="mt-4 pt-4 border-t border-gray-200">
                <button
                  onClick={handleDeleteNode}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
                >
                  Delete Node
                </button>
              </div>
            </div>
          ) : (
            <div>
              {generateYamlMutation.isPending ? (
                <div className="text-center py-8 text-gray-500">Generating YAML...</div>
              ) : yamlPreview ? (
                <>
                  {warnings.length > 0 && (
                    <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                      <h4 className="text-sm font-medium text-yellow-800 mb-2">Warnings</h4>
                      <ul className="text-xs text-yellow-700 space-y-1">
                        {warnings.map((w, i) => (
                          <li key={i}>• {w}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded-md text-xs overflow-x-auto">
                    {yamlPreview}
                  </pre>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  Drag components from the palette to start building
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[80vh] flex flex-col">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Builder State</h3>
            <div className="flex-1 overflow-auto mb-4">
              <textarea
                value={exportJson}
                readOnly
                rows={20}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(exportJson)
                  alert('Copied to clipboard!')
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Copy to Clipboard
              </button>
              <button
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Save as Template</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Name</label>
                <input
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="My Collector Config"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={templateDescription}
                  onChange={(e) => setTemplateDescription(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Optional description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Type</label>
                <select
                  value={templateType}
                  onChange={(e) => setTemplateType(e.target.value as any)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="composite">Composite</option>
                  <option value="metrics">Metrics</option>
                  <option value="logs">Logs</option>
                  <option value="traces">Traces</option>
                  <option value="routing">Routing</option>
                </select>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowSaveModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={!templateName || !yamlPreview}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function OtelBuilder(props: OtelBuilderProps) {
  return (
    <ReactFlowProvider>
      <OtelBuilderInner {...props} />
    </ReactFlowProvider>
  )
}


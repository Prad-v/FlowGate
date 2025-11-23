import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Types
export interface Template {
  id: string
  org_id: string | null
  name: string
  description?: string
  template_type: 'metrics' | 'logs' | 'traces' | 'routing' | 'composite'
  is_active: boolean
  current_version: number
  is_system_template: boolean
  default_version_id: string | null
  created_at: string
  updated_at: string | null
}

export interface TemplateVersion {
  id: string
  template_id: string
  version: number
  config_yaml: string
  description?: string
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export interface TemplateCreate {
  name: string
  description?: string
  template_type: 'metrics' | 'logs' | 'traces' | 'routing' | 'composite'
  org_id?: string
  config_yaml: string
  is_system_template?: boolean
}

export interface Deployment {
  id: string
  org_id: string
  name: string
  template_id: string
  template_version: number
  gateway_id?: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back'
  rollout_strategy: 'immediate' | 'canary' | 'staged'
  canary_percentage?: number
  started_at?: string
  completed_at?: string
  error_message?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface DeploymentCreate {
  name: string
  template_id: string
  template_version: number
  gateway_id?: string
  rollout_strategy?: 'immediate' | 'canary' | 'staged'
  canary_percentage?: number
  metadata?: Record<string, any>
}

export interface Gateway {
  id: string
  org_id: string
  name: string
  instance_id: string
  hostname?: string
  ip_address?: string
  status: 'registered' | 'active' | 'inactive' | 'error' | 'online' | 'offline' | 'unknown'
  last_seen?: string
  version?: string
  current_config_version?: number | null
  config_version?: number | null  // Alias for current_config_version
  metadata?: Record<string, any>
  // Basic OpAMP status fields for list view
  opamp_connection_status?: 'connected' | 'disconnected' | 'failed' | 'never_connected' | null
  opamp_remote_config_status?: 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED' | null
  opamp_transport_type?: string | null
  // Config management fields
  tags?: string[] | null
  last_config_version?: number | null
  last_config_status?: 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED' | null
  last_config_status_at?: string | null
  management_mode?: 'extension' | 'supervisor' | null
  created_at: string
  updated_at: string
}

export interface GatewayRegistrationResponse {
  id: string
  org_id: string
  name: string
  instance_id: string
  hostname?: string
  ip_address?: string
  status: 'registered' | 'active' | 'inactive' | 'error'
  last_seen?: string
  current_config_version?: number | null
  metadata?: Record<string, any>
  opamp_token: string
  opamp_endpoint: string
  created_at: string
  updated_at: string
}

export interface AgentHealth {
  status: 'healthy' | 'warning' | 'unhealthy' | 'offline'
  last_seen?: string
  seconds_since_last_seen?: number
  uptime_seconds?: number
  health_score: number
}

export interface AgentVersion {
  agent_version?: string
  otel_version?: string
  capabilities?: string[]
  metadata?: Record<string, any>
}

export interface AgentConfig {
  config_yaml: string
  config_version?: number
  deployment_id?: string
  last_updated?: string
}

export interface AgentMetrics {
  logs_processed?: number
  errors?: number
  latency_ms?: number
  last_updated?: string
}

export interface AgentStatus {
  gateway_id: string
  instance_id: string
  name: string
  health: AgentHealth
  version: AgentVersion
  config?: AgentConfig
  metrics?: AgentMetrics
  // OpAMP-specific fields
  opamp_connection_status?: 'connected' | 'disconnected' | 'failed' | 'never_connected' | null
  opamp_remote_config_status?: 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED' | null
  opamp_last_sequence_num?: number | null
  opamp_transport_type?: string | null
  opamp_agent_capabilities?: number | null
  opamp_agent_capabilities_decoded?: string[] | null
  opamp_agent_capabilities_display?: {
    bit_field_hex?: string
    bit_field_decimal?: number
    names?: string[]
  } | null
  opamp_server_capabilities?: number | null
  opamp_server_capabilities_decoded?: string[] | null
  opamp_server_capabilities_display?: {
    bit_field_hex?: string
    bit_field_decimal?: number
    names?: string[]
  } | null
  opamp_effective_config_hash?: string | null
  opamp_remote_config_hash?: string | null
  opamp_registration_failed?: boolean
  opamp_registration_failed_at?: string | null
  opamp_registration_failure_reason?: string | null
}

// OpAMP ReportsStatus interfaces
export interface AgentDescriptionIdentifiers {
  instance_uid?: string
  agent_type?: string
  agent_version?: string
  agent_id?: string
}

export interface AgentDescriptionOSRuntime {
  operating_system?: string
  architecture?: string
  labels?: Record<string, string>
  extensions?: string[]
}

export interface AgentDescriptionBuildInfo {
  'build.git.sha'?: string
  'build.timestamp'?: string
  'distro.name'?: string
}

export interface AgentDescription {
  identifiers?: AgentDescriptionIdentifiers
  os_runtime?: AgentDescriptionOSRuntime
  build_info?: AgentDescriptionBuildInfo | null
  identifying_attributes?: Array<{ key: string; value: string }>
  non_identifying_attributes?: Array<{ key: string; value: string }>
}

export interface EnhancedHealth {
  healthy?: boolean | null
  status_code?: 'healthy' | 'unhealthy' | 'degraded' | 'unknown'
  status_message?: string | null
  start_time_unix_nano?: number | null
  last_error?: string | null
  raw?: Record<string, any>
}

export interface PackageStatus {
  package_name: string
  package_version?: string | null
  package_type: string
  status: 'installed' | 'installing' | 'failed' | 'uninstalled'
  installed_at?: string | null
  error_message?: string | null
  package_hash?: string | null
  agent_reported_hash?: string | null
  server_offered_hash?: string | null
}

export interface ConnectionSettingInfo {
  settings_hash?: string | null
  status: 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED'
  applied_at?: string | null
  error_message?: string | null
}

export interface ConnectionSettingsHashes {
  own_metrics?: ConnectionSettingInfo | null
  own_logs?: ConnectionSettingInfo | null
  own_traces?: ConnectionSettingInfo | null
}

export interface HeartbeatTiming {
  last_seen?: string | null
  sequence_num?: number | null
  is_online: boolean
}

export interface ComponentMetadata {
  [key: string]: string | number | boolean
}

export interface AvailableComponent {
  component_id: string
  name: string
  component_type: 'receiver' | 'processor' | 'exporter' | 'extension' | 'unknown'
  version?: string
  metadata?: ComponentMetadata
  supported_data_types?: ('metrics' | 'logs' | 'traces')[]
  stability?: 'stable' | 'experimental' | 'deprecated'
  sub_components?: AvailableComponent[]
}

export interface AvailableComponents {
  components: AvailableComponent[]
  hash?: string
  last_updated?: string
}

export interface AgentDetailsResponse {
  instance_id: string
  gateway_id: string
  name: string
  management_mode?: 'extension' | 'supervisor' | null
  hostname?: string | null
  ip_address?: string | null
  last_seen?: string | null
  agent_version?: any
  agent_name?: string | null
  identifying_attributes?: Record<string, any>
  health?: EnhancedHealth
  opamp_connection_status?: 'connected' | 'disconnected' | 'failed' | 'never_connected' | null
  opamp_remote_config_status?: 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED' | null
  opamp_transport_type?: string | null
  opamp_last_sequence_num?: number | null
  opamp_agent_capabilities?: number | null
  opamp_agent_capabilities_decoded?: string[]
  opamp_agent_capabilities_display?: {
    bit_field_hex?: string
    bit_field_decimal?: number
    names?: string[]
  } | null
  opamp_server_capabilities?: number | null
  opamp_server_capabilities_decoded?: string[]
  opamp_server_capabilities_display?: {
    bit_field_hex?: string
    bit_field_decimal?: number
    names?: string[]
  } | null
  opamp_effective_config_hash?: string | null
  opamp_remote_config_hash?: string | null
  opamp_registration_failed?: boolean
  opamp_registration_failed_at?: string | null
  opamp_registration_failure_reason?: string | null
  connection_metrics?: {
    last_seen?: string | null
    sequence_num?: number | null
    transport_type?: string | null
  }
  agent_description?: AgentDescription
  package_statuses?: PackageStatus[]
  connection_settings_hashes?: ConnectionSettingsHashes
  heartbeat_timing?: HeartbeatTiming
  available_components?: AvailableComponents
  effective_config?: {
    hash?: string | null
    config_yaml?: string | null
    config_version?: number | null
    deployment_name?: string | null
    source?: string | null
  }
  current_config?: {
    config_yaml?: string
    config_version?: number | null
    deployment_id?: string | null
  } | null
  supervisor_status?: Record<string, any>
}

// Template API
export const templateApi = {
  list: async (orgId: string, isSystemTemplate?: boolean): Promise<Template[]> => {
    const params: any = {}
    if (isSystemTemplate !== undefined) {
      params.is_system_template = isSystemTemplate
    }
    const response = await apiClient.get('/templates', { params })
    return response.data
  },
  getSystemTemplates: async (): Promise<Template[]> => {
    const response = await apiClient.get('/templates', {
      params: { is_system_template: true },
    })
    return response.data
  },
  get: async (id: string, orgId: string): Promise<Template> => {
    const response = await apiClient.get(`/templates/${id}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  create: async (data: TemplateCreate): Promise<Template> => {
    const response = await apiClient.post('/templates', data)
    return response.data
  },
  update: async (id: string, orgId: string, data: Partial<TemplateCreate>): Promise<Template> => {
    const response = await apiClient.put(`/templates/${id}`, data, {
      params: { org_id: orgId },
    })
    return response.data
  },
  delete: async (id: string, orgId: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`, {
      params: { org_id: orgId },
    })
  },
  getVersions: async (id: string, orgId: string): Promise<TemplateVersion[]> => {
    const response = await apiClient.get(`/templates/${id}/versions`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  setDefaultVersion: async (templateId: string, version: number, orgId: string): Promise<Template> => {
    const response = await apiClient.put(`/templates/${templateId}/default-version`, {
      version,
    }, {
      params: { org_id: orgId },
    })
    return response.data
  },
  createFromGateway: async (gatewayId: string, name: string, description: string | undefined, templateType: string, isSystemTemplate: boolean, orgId: string): Promise<Template> => {
    const response = await apiClient.post('/templates/from-gateway', {
      gateway_id: gatewayId,
      name,
      description,
      template_type: templateType,
      is_system_template: isSystemTemplate,
    }, {
      params: { org_id: orgId },
    })
    return response.data
  },
  uploadTemplate: async (file: File, name: string, description: string | undefined, templateType: string, isSystemTemplate: boolean, orgId: string): Promise<Template> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    if (description) {
      formData.append('description', description)
    }
    formData.append('template_type', templateType)
    formData.append('is_system_template', isSystemTemplate.toString())
    
    const response = await apiClient.post('/templates/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      params: { org_id: orgId },
    })
    return response.data
  },
  validate: async (configYaml: string): Promise<any> => {
    const response = await apiClient.post('/templates/validate', {
      config_yaml: configYaml,
    })
    return response.data
  },
}

// OTEL Builder API
export interface ComponentMetadata {
  id: string
  name: string
  type: 'receiver' | 'processor' | 'exporter' | 'connector' | 'extension'
  description?: string
  doc_url?: string
  stability?: string
  language?: string
  tags?: string[]
  supported_signals?: string[]
  default_config?: Record<string, any>
}

export interface BuilderNode {
  id: string
  type: 'receiver' | 'processor' | 'exporter' | 'connector' | 'extension' | 'pipeline'
  component_id: string
  label?: string
  config?: Record<string, any>
  pipeline_type?: 'metrics' | 'logs' | 'traces'
  position?: { x: number; y: number }
}

export interface BuilderEdge {
  id: string
  source: string
  target: string
}

export interface BuilderGraph {
  nodes: BuilderNode[]
  edges: BuilderEdge[]
}

export interface BuilderGenerateResponse {
  yaml: string
  pipelines: Record<string, any>
  warnings: string[]
}

export const otelBuilderApi = {
  getComponents: async (
    componentType?: 'receiver' | 'processor' | 'exporter' | 'connector' | 'extension',
    source: 'static' | 'live' = 'static',
    search?: string
  ): Promise<Record<string, ComponentMetadata[]>> => {
    const params: any = { source }
    if (componentType) params.component_type = componentType
    if (search) params.search = search
    const response = await apiClient.get('/otel/components', { params })
    return response.data.items
  },
  generateConfig: async (graph: BuilderGraph): Promise<BuilderGenerateResponse> => {
    const response = await apiClient.post('/otel/builder/generate', graph)
    return response.data
  },
  parseConfig: async (yamlContent: string): Promise<BuilderGraph> => {
    const response = await apiClient.post('/otel/builder/parse', { yaml_content: yamlContent })
    return { nodes: response.data.nodes, edges: response.data.edges }
  },
}

// Deployment API
export const deploymentApi = {
  list: async (orgId: string): Promise<Deployment[]> => {
    const response = await apiClient.get('/deployments', {
      params: { org_id: orgId },
    })
    return response.data
  },
  get: async (id: string, orgId: string): Promise<Deployment> => {
    const response = await apiClient.get(`/deployments/${id}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  create: async (data: DeploymentCreate): Promise<Deployment> => {
    const response = await apiClient.post('/deployments', data)
    return response.data
  },
  rollback: async (id: string): Promise<Deployment> => {
    const response = await apiClient.post(`/deployments/${id}/rollback`)
    return response.data
  },
}

// Gateway API
export const gatewayApi = {
  list: async (orgId?: string): Promise<Gateway[]> => {
    const params = orgId ? { org_id: orgId } : {}
    const response = await apiClient.get('/gateways', { params })
    return response.data
  },
  get: async (id: string, orgId?: string): Promise<Gateway> => {
    const params = orgId ? { org_id: orgId } : {}
    const response = await apiClient.get(`/gateways/${id}`, { params })
    return response.data
  },
}

// Agent Management API
export const agentApi = {
  getHealth: async (gatewayId: string, orgId: string): Promise<AgentHealth> => {
    const response = await apiClient.get(`/gateways/${gatewayId}/health`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getVersion: async (gatewayId: string, orgId: string): Promise<AgentVersion> => {
    const response = await apiClient.get(`/gateways/${gatewayId}/version`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getConfig: async (gatewayId: string, orgId: string): Promise<AgentConfig> => {
    try {
      const response = await apiClient.get(`/gateways/${gatewayId}/config`, {
        params: { org_id: orgId },
      })
      return response.data
    } catch (error: any) {
      // Provide clear error message
      if (error.response?.status === 404) {
        throw new Error('Configuration not found. This agent may not have an active deployment.')
      } else if (error.response?.status === 403) {
        throw new Error('Access denied. You may not have permission to view this agent\'s configuration.')
      } else if (error.response?.data?.detail) {
        throw new Error(error.response.data.detail)
      } else if (error.message) {
        throw new Error(`Failed to retrieve configuration: ${error.message}`)
      } else {
        throw new Error('Unable to retrieve agent configuration. Please try again later.')
      }
    }
  },
  getMetrics: async (gatewayId: string, orgId: string): Promise<AgentMetrics> => {
    const response = await apiClient.get(`/gateways/${gatewayId}/metrics`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getStatus: async (gatewayId: string, orgId: string): Promise<AgentStatus> => {
    const response = await apiClient.get(`/gateways/${gatewayId}/status`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  listAgents: async (orgId: string): Promise<Gateway[]> => {
    const response = await apiClient.get('/gateways', {
      params: { org_id: orgId },
    })
    return response.data
  },
  restartRegistration: async (
    gatewayId: string,
    orgId: string,
    registrationToken: string
  ): Promise<GatewayRegistrationResponse> => {
    const response = await apiClient.post(
      `/gateways/${gatewayId}/restart-registration`,
      {},
      {
        params: { org_id: orgId },
        headers: {
          Authorization: `Bearer ${registrationToken}`,
        },
      }
    )
    return response.data
  },
}

// OpAMP Config Management API
export interface OpAMPConfigDeployment {
  id: string
  name: string
  config_version: number
  config_hash: string
  template_id?: string
  template_version?: number
  org_id: string
  rollout_strategy: 'immediate' | 'canary' | 'staged'
  canary_percentage?: number
  target_tags?: string[]
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'rolled_back'
  ignore_failures: boolean
  created_by?: string
  started_at?: string
  completed_at?: string
  error_message?: string
  created_at: string
  updated_at: string
}

export interface ConfigValidationError {
  level: 'error' | 'warning'
  message: string
  field?: string
  line?: number
}

export interface ConfigValidationResult {
  is_valid: boolean
  errors: ConfigValidationError[]
  warnings: ConfigValidationError[]
}

export interface DeploymentProgress {
  total: number
  applied: number
  applying: number
  failed: number
  pending: number
  success_rate: number
}

export interface AgentStatusBreakdown {
  gateway_id: string
  gateway_name: string
  instance_id: string
  status: string
  status_reported_at?: string
  error_message?: string
}

export interface ConfigDeploymentStatus {
  deployment_id: string
  deployment_name: string
  config_version: number
  status: string
  rollout_strategy: string
  canary_percentage?: number
  target_tags?: string[]
  progress: DeploymentProgress
  agent_statuses: AgentStatusBreakdown[]
  started_at?: string
  completed_at?: string
}

export interface ConfigAuditEntry {
  audit_id: string
  gateway_id: string
  gateway_name?: string
  instance_id?: string
  config_version: number
  config_hash: string
  status: string
  status_reported_at?: string
  error_message?: string
  effective_config_hash?: string
  created_at: string
  updated_at: string
}

export interface AgentConfigHistoryEntry {
  audit_id: string
  deployment_id: string
  deployment_name?: string
  config_version: number
  config_hash: string
  status: string
  status_reported_at?: string
  error_message?: string
  effective_config_hash?: string
  created_at: string
}

export const opampConfigApi = {
  createDeployment: async (
    orgId: string,
    data: {
      name: string
      config_yaml: string
      rollout_strategy?: 'immediate' | 'canary' | 'staged'
      canary_percentage?: number
      target_tags?: string[]
      ignore_failures?: boolean
      template_id?: string
      template_version?: number
    }
  ): Promise<OpAMPConfigDeployment> => {
    const response = await apiClient.post('/opamp-config/deployments', data, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getDeployments: async (orgId: string): Promise<OpAMPConfigDeployment[]> => {
    const response = await apiClient.get('/opamp-config/deployments', {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getDeployment: async (deploymentId: string, orgId: string): Promise<OpAMPConfigDeployment> => {
    const response = await apiClient.get(`/opamp-config/deployments/${deploymentId}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getDeploymentStatus: async (
    deploymentId: string,
    orgId: string
  ): Promise<ConfigDeploymentStatus> => {
    const response = await apiClient.get(`/opamp-config/deployments/${deploymentId}/status`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getDeploymentAudit: async (
    deploymentId: string,
    orgId: string
  ): Promise<ConfigAuditEntry[]> => {
    const response = await apiClient.get(`/opamp-config/deployments/${deploymentId}/audit`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  rollbackDeployment: async (
    deploymentId: string,
    orgId: string
  ): Promise<OpAMPConfigDeployment> => {
    const response = await apiClient.post(`/opamp-config/deployments/${deploymentId}/rollback`, {}, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  pushConfig: async (
    orgId: string,
    data: {
      config_yaml: string
      gateway_ids?: string[]
      target_tags?: string[]
      ignore_failures?: boolean
    }
  ): Promise<any> => {
    const response = await apiClient.post('/opamp-config/push', data, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getCurrentConfig: async (gatewayId: string, orgId: string): Promise<AgentConfig> => {
    const response = await apiClient.get('/opamp-config/current', {
      params: { gateway_id: gatewayId, org_id: orgId },
    })
    return response.data
  },
  
  validateConfig: async (configYaml: string): Promise<ConfigValidationResult> => {
    const response = await apiClient.post('/opamp-config/validate', configYaml, {
      headers: { 'Content-Type': 'text/plain' },
    })
    return response.data
  },
}

// Agent Tagging API
export interface AgentTag {
  id: string
  gateway_id: string
  tag: string
  created_at: string
}

export interface TagInfo {
  tag: string
  count: number
}

export const agentTagApi = {
  addTag: async (
    gatewayId: string,
    orgId: string,
    tag: string
  ): Promise<AgentTag> => {
    const response = await apiClient.post(
      `/agents/${gatewayId}/tags`,
      { tag },
      { params: { org_id: orgId } }
    )
    return response.data
  },
  
  removeTag: async (
    gatewayId: string,
    orgId: string,
    tag: string
  ): Promise<void> => {
    await apiClient.delete(`/agents/${gatewayId}/tags/${encodeURIComponent(tag)}`, {
      params: { org_id: orgId },
    })
  },
  
  getTags: async (gatewayId: string, orgId: string): Promise<string[]> => {
    const response = await apiClient.get(`/agents/${gatewayId}/tags`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  getAllTags: async (orgId: string): Promise<TagInfo[]> => {
    const response = await apiClient.get('/agents/tags', {
      params: { org_id: orgId },
    })
    return response.data
  },
  
  bulkTag: async (
    orgId: string,
    gatewayIds: string[],
    tags: string[]
  ): Promise<{ message: string }> => {
    const response = await apiClient.post(
      '/agents/tags/bulk',
      { gateway_ids: gatewayIds, tags },
      { params: { org_id: orgId } }
    )
    return response.data
  },
  
  bulkRemoveTags: async (
    orgId: string,
    gatewayIds: string[],
    tags: string[]
  ): Promise<{ message: string }> => {
    const response = await apiClient.post(
      '/agents/tags/bulk-remove',
      { gateway_ids: gatewayIds, tags },
      { params: { org_id: orgId } }
    )
    return response.data
  },
}

// Supervisor API
export const supervisorApi = {
  listAgents: async (orgId: string): Promise<any[]> => {
    const response = await apiClient.get('/supervisor/agents', {
      params: { org_id: orgId },
    })
    return response.data
  },
  getStatus: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.get(`/supervisor/agents/${instanceId}/status`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getLogs: async (instanceId: string, orgId: string, lines: number = 100): Promise<any> => {
    const response = await apiClient.get(`/supervisor/agents/${instanceId}/logs`, {
      params: { org_id: orgId, lines },
    })
    return response.data
  },
  restartAgent: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.post(`/supervisor/agents/${instanceId}/restart`, {}, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getAgentDescription: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.get(`/supervisor/agents/${instanceId}/description`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  pushConfig: async (instanceId: string, configYaml: string, orgId: string): Promise<any> => {
    const response = await apiClient.post(`/supervisor/ui/agents/${instanceId}/config`, {
      config_yaml: configYaml,
    }, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getEffectiveConfig: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.get(`/supervisor/ui/agents/${instanceId}/effective-config`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  requestEffectiveConfig: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.post(`/supervisor/ui/agents/${instanceId}/request-effective-config`, {}, {
      params: { org_id: orgId },
    })
    return response.data
  },
  requestAvailableComponents: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.post(`/supervisor/ui/agents/${instanceId}/request-available-components`, {}, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getConfigRequestStatus: async (instanceId: string, trackingId: string, orgId: string): Promise<any> => {
    const response = await apiClient.get(`/supervisor/ui/agents/${instanceId}/config-requests/${trackingId}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
  compareConfig: async (instanceId: string, standardConfigId: string | null, standardConfigYaml: string | null, orgId: string): Promise<any> => {
    const response = await apiClient.post(`/supervisor/ui/agents/${instanceId}/compare-config`, {
      standard_config_id: standardConfigId,
      standard_config_yaml: standardConfigYaml,
    }, {
      params: { org_id: orgId },
    })
    return response.data
  },
  getDefaultSystemTemplate: async (): Promise<any> => {
    const response = await apiClient.get('/system-templates/default')
    return response.data
  },
  getAgentDetails: async (instanceId: string, orgId: string): Promise<AgentDetailsResponse> => {
    const response = await apiClient.get(`/supervisor/ui/agents/${instanceId}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
}

// Settings API
export interface AIProviderConfig {
  provider_type: 'litellm' | 'openai' | 'anthropic' | 'custom'
  provider_name: string
  api_key?: string
  endpoint?: string
  model?: string
  config?: Record<string, any>
  is_active: boolean
}

export interface AISettingsResponse {
  provider_config: AIProviderConfig | null
}

export const settingsApi = {
  get: async (): Promise<any> => {
    const response = await apiClient.get('/settings')
    return response.data
  },
  update: async (settings: { gateway_management_mode: string }): Promise<any> => {
    const response = await apiClient.put('/settings', settings)
    return response.data
  },
  getGatewayManagementMode: async (): Promise<{ gateway_management_mode: string }> => {
    const response = await apiClient.get('/settings/gateway-management-mode')
    return response.data
  },
}

// AI Settings API
export const aiSettingsApi = {
  get: async (): Promise<AISettingsResponse> => {
    const response = await apiClient.get('/settings/ai')
    return response.data
  },
  update: async (providerConfig: AIProviderConfig): Promise<AISettingsResponse> => {
    const response = await apiClient.put('/settings/ai', {
      provider_config: providerConfig,
    })
    return response.data
  },
  test: async (providerConfig: AIProviderConfig): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/settings/ai/test', {
      provider_config: providerConfig,
    })
    return response.data
  },
  getModels: async (providerConfig: AIProviderConfig): Promise<{ success: boolean; message: string; models: string[] }> => {
    const response = await apiClient.post('/settings/ai/models', {
      provider_config: providerConfig,
    })
    return response.data
  },
}

// MCP Server API
export interface MCPServerConfig {
  server_type: 'grafana' | 'aws' | 'gcp' | 'custom'
  server_name: string
  endpoint_url?: string
  auth_type: 'oauth' | 'custom_header' | 'no_auth'
  auth_config?: Record<string, any>
  scope: 'personal' | 'tenant'
  is_enabled: boolean
  metadata?: Record<string, any>
}

export interface MCPServerCreate {
  server_type: 'grafana' | 'aws' | 'gcp' | 'custom'
  server_name: string
  endpoint_url?: string
  auth_type?: 'oauth' | 'custom_header' | 'no_auth'
  auth_config?: Record<string, any>
  scope?: 'personal' | 'tenant'
  metadata?: Record<string, any>
}

export interface MCPServerUpdate {
  server_name?: string
  endpoint_url?: string
  auth_type?: 'oauth' | 'custom_header' | 'no_auth'
  auth_config?: Record<string, any>
  scope?: 'personal' | 'tenant'
  metadata?: Record<string, any>
}

export interface MCPServerResponse {
  id: string
  org_id: string
  server_type: string
  server_name: string
  endpoint_url?: string | null
  auth_type: string
  auth_config?: Record<string, any> | null
  scope: string
  is_enabled: boolean
  is_active: boolean
  last_tested_at?: string | null
  last_test_status?: string | null
  last_test_error?: string | null
  discovered_resources?: Record<string, any> | null
  metadata?: Record<string, any> | null
  created_at: string
  updated_at?: string | null
}

export interface MCPServerListResponse {
  servers: MCPServerResponse[]
  total: number
}

export interface MCPConnectionTestResponse {
  success: boolean
  message: string
  discovered_resources?: Record<string, any> | null
  error?: string | null
}

export interface MCPResourceDiscoveryResponse {
  success: boolean
  resources: Record<string, any>
  message?: string | null
  error?: string | null
}

export interface MCPServerTypeInfo {
  server_type: string
  display_name: string
  description: string
  required_fields: string[]
  optional_fields: string[]
  auth_types: string[]
  example_config?: Record<string, any>
}

export const mcpServerApi = {
  getServers: async (filters?: {
    server_type?: string
    is_enabled?: boolean
    scope?: string
  }): Promise<MCPServerListResponse> => {
    const response = await apiClient.get('/settings/mcp/servers', { params: filters })
    return response.data
  },
  getServer: async (serverId: string): Promise<MCPServerResponse> => {
    const response = await apiClient.get(`/settings/mcp/servers/${serverId}`)
    return response.data
  },
  createServer: async (serverData: MCPServerCreate): Promise<MCPServerResponse> => {
    const response = await apiClient.post('/settings/mcp/servers', serverData)
    return response.data
  },
  updateServer: async (serverId: string, serverData: MCPServerUpdate): Promise<MCPServerResponse> => {
    const response = await apiClient.put(`/settings/mcp/servers/${serverId}`, serverData)
    return response.data
  },
  deleteServer: async (serverId: string): Promise<void> => {
    await apiClient.delete(`/settings/mcp/servers/${serverId}`)
  },
  testConnection: async (serverId: string): Promise<MCPConnectionTestResponse> => {
    const response = await apiClient.post(`/settings/mcp/servers/${serverId}/test`)
    return response.data
  },
  discoverResources: async (serverId: string): Promise<MCPResourceDiscoveryResponse> => {
    const response = await apiClient.post(`/settings/mcp/servers/${serverId}/discover`)
    return response.data
  },
  enableServer: async (serverId: string): Promise<MCPServerResponse> => {
    const response = await apiClient.post(`/settings/mcp/servers/${serverId}/enable`)
    return response.data
  },
  disableServer: async (serverId: string): Promise<MCPServerResponse> => {
    const response = await apiClient.post(`/settings/mcp/servers/${serverId}/disable`)
    return response.data
  },
  getServerTypes: async (): Promise<MCPServerTypeInfo[]> => {
    const response = await apiClient.get('/settings/mcp/servers/types')
    return response.data
  },
}

// Log Transformation API
export interface LogFormatTemplate {
  id: string
  format_name: string
  display_name: string
  format_type: 'source' | 'destination' | 'both'
  description?: string | null
  sample_logs?: string | null
  parser_config?: Record<string, any> | null
  schema?: Record<string, any> | null
  is_system_template: boolean
  created_at: string
  updated_at?: string | null
}

export interface LogFormatTemplateListResponse {
  templates: LogFormatTemplate[]
  total: number
}

export interface LogTransformRequest {
  source_format?: string | null
  destination_format?: string | null // Deprecated, kept for backward compatibility
  sample_logs: string
  target_json?: string | null // Optional - can be generated from ai_prompt
  ai_prompt?: string | null // Optional - natural language description of desired output
  custom_source_parser?: Record<string, any> | null
}

export interface GenerateTargetJsonRequest {
  source_format?: string | null
  sample_logs: string
  ai_prompt: string
}

export interface GenerateTargetJsonResponse {
  success: boolean
  target_json: string
  errors: string[]
  warnings: string[]
}

export interface LogTransformResponse {
  success: boolean
  otel_config: string
  warnings: string[]
  errors: string[]
  recommendations?: string[] | null
}

export interface FormatRecommendation {
  format_name: string
  display_name: string
  confidence_score: number
  reasoning: string
  compatibility_score?: number | null
}

export interface FormatRecommendationRequest {
  source_format?: string | null
  sample_logs?: string | null
  use_case?: string | null
}

export interface FormatRecommendationResponse {
  success: boolean
  recommendations: FormatRecommendation[]
  message?: string | null
}

export interface ConfigValidationRequest {
  config: string
  sample_logs?: string | null
}

export interface ConfigValidationResponse {
  valid: boolean
  errors: string[]
  warnings: string[]
}

export interface DryRunRequest {
  config: string
  sample_logs: string
}

export interface DryRunResponse {
  success: boolean
  transformed_logs: Record<string, any>[]
  errors: string[]
}

export const logTransformationApi = {
  getFormats: async (formatType?: string): Promise<LogFormatTemplateListResponse> => {
    const params: any = {}
    if (formatType) params.format_type = formatType
    const response = await apiClient.get('/log-transformer/formats', { params })
    return response.data
  },
  getFormat: async (formatName: string): Promise<LogFormatTemplate> => {
    const response = await apiClient.get(`/log-transformer/formats/${formatName}`)
    return response.data
  },
  transformLogs: async (request: LogTransformRequest): Promise<LogTransformResponse> => {
    const response = await apiClient.post('/log-transformer/transform', request)
    return response.data
  },
  generateTargetJson: async (request: GenerateTargetJsonRequest): Promise<GenerateTargetJsonResponse> => {
    const response = await apiClient.post('/log-transformer/generate-target', request)
    return response.data
  },
  getRecommendations: async (request: FormatRecommendationRequest): Promise<FormatRecommendationResponse> => {
    const response = await apiClient.post('/log-transformer/recommend', request)
    return response.data
  },
  validateConfig: async (request: ConfigValidationRequest): Promise<ConfigValidationResponse> => {
    const response = await apiClient.post('/log-transformer/validate', request)
    return response.data
  },
  dryRun: async (request: DryRunRequest): Promise<DryRunResponse> => {
    const response = await apiClient.post('/log-transformer/dry-run', request)
    return response.data
  },
}

export default apiClient

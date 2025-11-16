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
  getAgentDetails: async (instanceId: string, orgId: string): Promise<any> => {
    const response = await apiClient.get(`/supervisor/ui/agents/${instanceId}`, {
      params: { org_id: orgId },
    })
    return response.data
  },
}

// Settings API
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

export default apiClient

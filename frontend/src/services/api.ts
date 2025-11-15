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
  org_id: string
  name: string
  description?: string
  template_type: 'metric' | 'log' | 'trace' | 'routing'
  is_active: boolean
  current_version: number
  created_at: string
  updated_at: string
}

export interface TemplateVersion {
  id: string
  template_id: string
  version: number
  change_summary?: string
  is_deployed: boolean
  created_at: string
  created_by?: string
}

export interface TemplateCreate {
  name: string
  description?: string
  template_type: 'metric' | 'log' | 'trace' | 'routing'
  config_yaml: string
  change_summary?: string
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
  list: async (): Promise<Template[]> => {
    const response = await apiClient.get('/templates')
    return response.data
  },
  get: async (id: string): Promise<Template> => {
    const response = await apiClient.get(`/templates/${id}`)
    return response.data
  },
  create: async (data: TemplateCreate): Promise<Template> => {
    const response = await apiClient.post('/templates', data)
    return response.data
  },
  update: async (id: string, data: Partial<TemplateCreate>): Promise<Template> => {
    const response = await apiClient.put(`/templates/${id}`, data)
    return response.data
  },
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`)
  },
  getVersions: async (id: string): Promise<TemplateVersion[]> => {
    const response = await apiClient.get(`/templates/${id}/versions`)
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
  list: async (): Promise<Deployment[]> => {
    const response = await apiClient.get('/deployments')
    return response.data
  },
  get: async (id: string): Promise<Deployment> => {
    const response = await apiClient.get(`/deployments/${id}`)
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

export default apiClient

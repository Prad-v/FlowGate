/** Authentication service for frontend */

import apiClient from './api'

export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  org_id?: string
  oidc_provider_id?: string
  password_changed_at?: string
  last_login_at?: string
  created_at: string
  updated_at?: string
}

export interface LoginRequest {
  username_or_email: string
  password: string
  org_id?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
  requires_password_change: boolean
}

export interface ChangePasswordRequest {
  old_password?: string
  new_password: string
}

export interface OIDCProvider {
  id: string
  name: string
  provider_type: 'direct' | 'proxy'
  is_active: boolean
  is_default: boolean
  org_id?: string
}

class AuthService {
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private tokenExpiry: number | null = null

  /**
   * Login with username/email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials)
    const data = response.data
    
    // Store tokens in memory (not localStorage for security)
    this.accessToken = data.access_token
    this.refreshToken = data.refresh_token
    this.tokenExpiry = Date.now() + (data.expires_in * 1000)
    
    // Set up token refresh interceptor
    this.setupTokenRefresh()
    
    return data
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Ignore errors on logout
    } finally {
      this.clearTokens()
    }
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  }

  /**
   * Change password
   */
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await apiClient.post('/auth/change-password', data)
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await apiClient.post<{
      access_token: string
      token_type: string
      expires_in: number
    }>('/auth/refresh', {
      refresh_token: this.refreshToken
    })

    this.accessToken = response.data.access_token
    this.tokenExpiry = Date.now() + (response.data.expires_in * 1000)

    return response.data.access_token
  }

  /**
   * Get available OIDC providers
   */
  async getOIDCProviders(orgId?: string): Promise<OIDCProvider[]> {
    const params = orgId ? { org_id: orgId } : {}
    const response = await apiClient.get<OIDCProvider[]>('/auth/oidc/providers', { params })
    return response.data
  }

  /**
   * Initiate OIDC login flow
   */
  async initiateOIDCLogin(providerId: string, redirectUri: string, state?: string): Promise<void> {
    try {
      const params = new URLSearchParams({
        redirect_uri: redirectUri,
        ...(state && { state })
      })
      const response = await apiClient.get<{ authorization_url: string }>(
        `/auth/oidc/${providerId}/authorize?${params.toString()}`
      )
      window.location.href = response.data.authorization_url
    } catch (error) {
      console.error('Failed to initiate OIDC login:', error)
      throw error
    }
  }

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    // Check if token is expired
    if (this.tokenExpiry && Date.now() >= this.tokenExpiry) {
      // Token expired, try to refresh
      this.refreshAccessToken().catch(() => {
        this.clearTokens()
      })
    }
    return this.accessToken
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.accessToken !== null && 
           (this.tokenExpiry === null || Date.now() < this.tokenExpiry)
  }

  /**
   * Clear all tokens
   */
  clearTokens(): void {
    this.accessToken = null
    this.refreshToken = null
    this.tokenExpiry = null
  }

  /**
   * Set up automatic token refresh
   */
  private setupTokenRefresh(): void {
    // Refresh token 5 minutes before expiry
    if (this.tokenExpiry) {
      const refreshTime = this.tokenExpiry - Date.now() - (5 * 60 * 1000)
      if (refreshTime > 0) {
        setTimeout(() => {
          this.refreshAccessToken().catch(() => {
            this.clearTokens()
          })
        }, refreshTime)
      }
    }
  }
}

// Export singleton instance
export const authService = new AuthService()

// Set up axios interceptor to add auth token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = authService.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Set up axios interceptor to handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await authService.refreshAccessToken()
        // Retry original request with new token
        const token = authService.getAccessToken()
        if (token) {
          originalRequest.headers.Authorization = `Bearer ${token}`
        }
        return apiClient(originalRequest)
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        authService.clearTokens()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)


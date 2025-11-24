/** Login component with local and OIDC authentication */

import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authService, OIDCProvider } from '../services/auth'

export default function Login() {
  const [usernameOrEmail, setUsernameOrEmail] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [requiresPasswordChange, setRequiresPasswordChange] = useState(false)
  const [oidcProviders, setOidcProviders] = useState<OIDCProvider[]>([])
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login, changePassword, user } = useAuth()

  useEffect(() => {
    // Check for OIDC callback
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const providerId = searchParams.get('provider_id')

    if (code && providerId) {
      handleOIDCCallback(providerId, code, state)
    } else {
      // Load OIDC providers
      loadOIDCProviders()
    }
  }, [searchParams])

  useEffect(() => {
    // If user is authenticated and password changed, redirect
    if (user && !requiresPasswordChange) {
      const redirectTo = searchParams.get('redirect') || '/'
      navigate(redirectTo)
    }
  }, [user, requiresPasswordChange, navigate, searchParams])

  const loadOIDCProviders = async () => {
    try {
      const providers = await authService.getOIDCProviders()
      setOidcProviders(providers.filter(p => p.is_active))
    } catch (error) {
      console.error('Failed to load OIDC providers:', error)
    }
  }

  const handleOIDCCallback = async (providerId: string, code: string, state: string | null) => {
    setIsLoading(true)
    setError('')
    
    try {
      const redirectUri = `${window.location.origin}${window.location.pathname}`
      // OIDC callback is handled by backend - redirect to backend callback endpoint
      window.location.href = `/api/v1/auth/oidc/${providerId}/callback?code=${code}&state=${state || ''}&redirect_uri=${encodeURIComponent(redirectUri)}`
    } catch (err: any) {
      setError(err.response?.data?.detail || 'OIDC authentication failed')
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await authService.login({
        username_or_email: usernameOrEmail,
        password: password,
      })

      if (response.requires_password_change) {
        setRequiresPasswordChange(true)
      } else {
        await login({
          username_or_email: usernameOrEmail,
          password: password,
        })
        navigate(searchParams.get('redirect') || '/')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsLoading(true)

    try {
      await changePassword({
        new_password: newPassword,
        // old_password not required for first login
      })
      setRequiresPasswordChange(false)
      navigate(searchParams.get('redirect') || '/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password')
    } finally {
      setIsLoading(false)
    }
  }

  const handleOIDCLogin = async (providerId: string) => {
    try {
      const redirectUri = `${window.location.origin}${window.location.pathname}`
      await authService.initiateOIDCLogin(providerId, redirectUri)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initiate OIDC login')
    }
  }

  if (requiresPasswordChange) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Change Password
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              You must change your password before continuing
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handlePasswordChange}>
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="text-sm text-red-800">{error}</div>
              </div>
            )}
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="new-password" className="sr-only">
                  New Password
                </label>
                <input
                  id="new-password"
                  name="new-password"
                  type="password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="New Password (min 8 characters)"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="confirm-password" className="sr-only">
                  Confirm Password
                </label>
                <input
                  id="confirm-password"
                  name="confirm-password"
                  type="password"
                  required
                  className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                  placeholder="Confirm Password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {isLoading ? 'Changing Password...' : 'Change Password'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to FlowGate
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Use your credentials or OIDC provider
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username-email" className="sr-only">
                Username or Email
              </label>
              <input
                id="username-email"
                name="username-email"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Username or Email"
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
        </form>

        {oidcProviders.length > 0 && (
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-50 text-gray-500">Or continue with</span>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-3">
              {oidcProviders.map((provider) => (
                <button
                  key={provider.id}
                  type="button"
                  onClick={() => handleOIDCLogin(provider.id)}
                  className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                >
                  <span>{provider.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}


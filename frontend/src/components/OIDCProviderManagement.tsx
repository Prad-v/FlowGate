/** OIDC Provider Management Component */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { oidcProviderApi, OIDCProvider, OIDCProviderCreate, OIDCProviderUpdate } from '../services/api'

export default function OIDCProviderManagement() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingProvider, setEditingProvider] = useState<OIDCProvider | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const { data: providers, isLoading } = useQuery({
    queryKey: ['oidc-providers'],
    queryFn: () => oidcProviderApi.list(),
  })

  const createMutation = useMutation({
    mutationFn: (data: OIDCProviderCreate) => oidcProviderApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oidc-providers'] })
      setShowForm(false)
      setMessage('OIDC provider created successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: OIDCProviderUpdate }) =>
      oidcProviderApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oidc-providers'] })
      setShowForm(false)
      setEditingProvider(null)
      setMessage('OIDC provider updated successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => oidcProviderApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['oidc-providers'] })
      setMessage('OIDC provider deleted successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })


  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data: OIDCProviderCreate | OIDCProviderUpdate = {
      name: formData.get('name') as string,
      provider_type: formData.get('provider_type') as 'direct' | 'proxy',
      issuer_url: formData.get('issuer_url') as string || undefined,
      client_id: formData.get('client_id') as string || undefined,
      client_secret: formData.get('client_secret') as string || undefined,
      authorization_endpoint: formData.get('authorization_endpoint') as string || undefined,
      token_endpoint: formData.get('token_endpoint') as string || undefined,
      userinfo_endpoint: formData.get('userinfo_endpoint') as string || undefined,
      proxy_url: formData.get('proxy_url') as string || undefined,
      scopes: formData.get('scopes') as string || 'openid,profile,email',
      is_active: formData.get('is_active') === 'true',
      is_default: formData.get('is_default') === 'true',
    }

    if (editingProvider) {
      updateMutation.mutate({ id: editingProvider.id, data })
    } else {
      createMutation.mutate(data as OIDCProviderCreate)
    }
  }

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading OIDC providers...</div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-medium text-gray-900">OIDC Providers</h2>
          <p className="mt-1 text-sm text-gray-500">
            Configure OIDC/OAuth providers for single sign-on
          </p>
        </div>
        <button
          onClick={() => {
            setEditingProvider(null)
            setShowForm(true)
          }}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
        >
          Add Provider
        </button>
      </div>

      {message && (
        <div className={`mx-6 mt-4 rounded-md p-4 ${
          message.includes('Error') || message.includes('failed')
            ? 'bg-red-50 border border-red-200'
            : 'bg-green-50 border border-green-200'
        }`}>
          <p className={`text-sm ${
            message.includes('Error') || message.includes('failed')
              ? 'text-red-800'
              : 'text-green-800'
          }`}>
            {message}
          </p>
        </div>
      )}

      {showForm ? (
        <div className="px-6 py-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <input
                type="text"
                name="name"
                required
                defaultValue={editingProvider?.name}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Provider Type</label>
              <select
                name="provider_type"
                required
                defaultValue={editingProvider?.provider_type}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="direct">Direct (Okta, Azure AD, Google)</option>
                <option value="proxy">OAuth Proxy</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Client ID</label>
              <input
                type="text"
                name="client_id"
                required
                defaultValue={editingProvider?.client_id}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Client Secret</label>
              <input
                type="password"
                name="client_secret"
                placeholder={editingProvider ? 'Leave blank to keep existing' : ''}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Issuer URL (for direct providers)</label>
              <input
                type="url"
                name="issuer_url"
                placeholder="https://your-provider.com/.well-known/openid-configuration"
                defaultValue={editingProvider?.issuer_url}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Authorization Endpoint (optional, auto-discovered if not provided)</label>
              <input
                type="url"
                name="authorization_endpoint"
                defaultValue={editingProvider?.authorization_endpoint}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Token Endpoint (optional, auto-discovered if not provided)</label>
              <input
                type="url"
                name="token_endpoint"
                defaultValue={editingProvider?.token_endpoint}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">UserInfo Endpoint (optional, auto-discovered if not provided)</label>
              <input
                type="url"
                name="userinfo_endpoint"
                defaultValue={editingProvider?.userinfo_endpoint}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Proxy URL (for proxy providers)</label>
              <input
                type="url"
                name="proxy_url"
                defaultValue={editingProvider?.proxy_url}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Scopes (comma-separated)</label>
              <input
                type="text"
                name="scopes"
                defaultValue={editingProvider?.scopes || 'openid,profile,email'}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>

            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_active"
                  value="true"
                  defaultChecked={editingProvider?.is_active ?? true}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Active</span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  name="is_default"
                  value="true"
                  defaultChecked={editingProvider?.is_default ?? false}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Default Provider</span>
              </label>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setEditingProvider(null)
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
              >
                {editingProvider ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="px-6 py-5">
          {providers && providers.length > 0 ? (
            <div className="space-y-3">
              {providers.map((provider) => (
                <div
                  key={provider.id}
                  className="border border-gray-200 rounded-lg p-4"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{provider.name}</h4>
                      <p className="text-sm text-gray-500 mt-1">
                        Type: {provider.provider_type}
                        {provider.client_id && ` | Client ID: ${provider.client_id}`}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        {provider.is_active ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            Inactive
                          </span>
                        )}
                        {provider.provider_type === 'direct' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            Direct
                          </span>
                        )}
                        {provider.provider_type === 'proxy' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                            Proxy
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setEditingProvider(provider)
                          setShowForm(true)
                        }}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          if (confirm(`Delete ${provider.name}?`)) {
                            deleteMutation.mutate(provider.id)
                          }
                        }}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-500">No OIDC providers configured</p>
              <button
                onClick={() => setShowForm(true)}
                className="mt-4 text-blue-600 hover:text-blue-800 text-sm font-medium"
              >
                Create your first OIDC provider
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}


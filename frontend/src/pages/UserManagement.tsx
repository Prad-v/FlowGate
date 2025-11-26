/** User Management Page for RBAC */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rbacApi, Role, UserRole, userManagementApi, organizationApi, User, Organization } from '../services/api'
import { useAuth } from '../contexts/AuthContext'

type TabType = 'users' | 'organizations' | 'associations'

export default function UserManagement() {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabType>('users')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null)
  const [showUserForm, setShowUserForm] = useState(false)
  const [showOrgForm, setShowOrgForm] = useState(false)
  const [showRoleAssignment, setShowRoleAssignment] = useState(false)
  const [showOrgAssignment, setShowOrgAssignment] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  // Check if user has permission to manage users
  const canManageUsers = currentUser?.is_superuser || false // TODO: Check for users:write permission
  const isSuperAdmin = currentUser?.is_superuser || false

  // Fetch data
  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => userManagementApi.list(),
    enabled: !!currentUser && canManageUsers,
  })

  const { data: organizations, isLoading: orgsLoading } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationApi.list(),
    enabled: !!currentUser && isSuperAdmin, // Only super admin can manage organizations
  })

  const { data: roles } = useQuery({
    queryKey: ['rbac-roles'],
    queryFn: () => rbacApi.getRoles(),
  })

  const { data: userRoles } = useQuery({
    queryKey: ['rbac-user-roles', selectedUser?.id],
    queryFn: () => selectedUser ? rbacApi.getUserRoles(selectedUser.id) : Promise.resolve([]),
    enabled: !!selectedUser && showRoleAssignment,
  })

  // Mutations
  const createUserMutation = useMutation({
    mutationFn: (data: any) => userManagementApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowUserForm(false)
      setMessage('User created successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => userManagementApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowUserForm(false)
      setSelectedUser(null)
      setMessage('User updated successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const createOrgMutation = useMutation({
    mutationFn: (data: any) => organizationApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      setShowOrgForm(false)
      setMessage('Organization created successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const updateOrgMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => organizationApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations'] })
      setShowOrgForm(false)
      setSelectedOrg(null)
      setMessage('Organization updated successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const assignRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rbacApi.assignRole(userId, { role_id: roleId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac-user-roles'] })
      setMessage('Role assigned successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rbacApi.removeRole(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac-user-roles', 'users'] })
      setMessage('Role removed successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const assignOrgMutation = useMutation({
    mutationFn: ({ userId, orgId }: { userId: string; orgId: string }) =>
      userManagementApi.assignToOrg(userId, orgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowOrgAssignment(false)
      setMessage('User assigned to organization successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const removeOrgMutation = useMutation({
    mutationFn: ({ userId, orgId }: { userId: string; orgId: string }) =>
      userManagementApi.removeFromOrg(userId, orgId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setMessage('User removed from organization successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  const handleUserSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      email: formData.get('email') as string,
      username: formData.get('username') as string,
      password: formData.get('password') as string || undefined,
      full_name: formData.get('full_name') as string || undefined,
      org_id: formData.get('org_id') as string || undefined,
      is_active: formData.get('is_active') === 'true',
      is_superuser: formData.get('is_superuser') === 'true',
    }

    if (selectedUser) {
      updateUserMutation.mutate({ id: selectedUser.id, data })
    } else {
      if (!data.password) {
        setMessage('Password is required for new users')
        setTimeout(() => setMessage(null), 5000)
        return
      }
      createUserMutation.mutate(data)
    }
  }

  const handleOrgSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      name: formData.get('name') as string,
      slug: formData.get('slug') as string,
      is_active: formData.get('is_active') === 'true',
    }

    if (selectedOrg) {
      updateOrgMutation.mutate({ id: selectedOrg.id, data })
    } else {
      createOrgMutation.mutate(data)
    }
  }

  if (!currentUser || !canManageUsers) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-900">Access Denied</h2>
          <p className="mt-2 text-gray-600">User management access required</p>
        </div>
      </div>
    )
  }

  if (usersLoading || orgsLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <div className="text-center py-12">
          <div className="text-gray-500">Loading...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">User & Organization Management</h1>
        <p className="mt-2 text-sm text-gray-600">
          Manage users, organizations, and assignments
        </p>
      </div>

      {message && (
        <div className={`mb-6 rounded-md p-4 ${
          message.includes('Error')
            ? 'bg-red-50 border border-red-200'
            : 'bg-green-50 border border-green-200'
        }`}>
          <p className={`text-sm ${
            message.includes('Error')
              ? 'text-red-800'
              : 'text-green-800'
          }`}>
            {message}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('users')}
            className={`${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Users
          </button>
          {isSuperAdmin && (
            <>
              <button
                onClick={() => setActiveTab('organizations')}
                className={`${
                  activeTab === 'organizations'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Organizations
              </button>
              <button
                onClick={() => setActiveTab('associations')}
                className={`${
                  activeTab === 'associations'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                User-Org Associations
              </button>
            </>
          )}
        </nav>
      </div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">Users</h2>
            <button
              onClick={() => {
                setSelectedUser(null)
                setShowUserForm(true)
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Add User
            </button>
          </div>

          {showUserForm ? (
            <div className="px-6 py-5">
              <form onSubmit={handleUserSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Email *</label>
                  <input
                    type="email"
                    name="email"
                    required
                    defaultValue={selectedUser?.email}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Username *</label>
                  <input
                    type="text"
                    name="username"
                    required
                    defaultValue={selectedUser?.username}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                {!selectedUser && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Password *</label>
                    <input
                      type="password"
                      name="password"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700">Full Name</label>
                  <input
                    type="text"
                    name="full_name"
                    defaultValue={selectedUser?.full_name}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                {isSuperAdmin && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Organization</label>
                    <select
                      name="org_id"
                      defaultValue={selectedUser?.org_id || ''}
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    >
                      <option value="">None</option>
                      {organizations?.map((org) => (
                        <option key={org.id} value={org.id}>{org.name}</option>
                      ))}
                    </select>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="is_active"
                      value="true"
                      defaultChecked={selectedUser?.is_active ?? true}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Active</span>
                  </label>
                  {isSuperAdmin && (
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        name="is_superuser"
                        value="true"
                        defaultChecked={selectedUser?.is_superuser ?? false}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="ml-2 text-sm text-gray-700">Super User</span>
                    </label>
                  )}
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowUserForm(false)
                      setSelectedUser(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createUserMutation.isPending || updateUserMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
                  >
                    {selectedUser ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="px-6 py-5">
              {users && users.length > 0 ? (
                <div className="space-y-3">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">
                            {user.full_name || user.username}
                          </h4>
                          <p className="text-sm text-gray-500 mt-1">{user.email}</p>
                          <div className="flex items-center gap-2 mt-2">
                            {user.is_superuser && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                Super Admin
                              </span>
                            )}
                            {user.is_active ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                Inactive
                              </span>
                            )}
                            {user.org_id && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                {organizations?.find(o => o.id === user.org_id)?.name || 'Org'}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => {
                              setSelectedUser(user)
                              setShowRoleAssignment(true)
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Manage Roles
                          </button>
                          <button
                            onClick={() => {
                              setSelectedUser(user)
                              setShowUserForm(true)
                            }}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No users found
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Organizations Tab */}
      {activeTab === 'organizations' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">Organizations</h2>
            <button
              onClick={() => {
                setSelectedOrg(null)
                setShowOrgForm(true)
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Add Organization
            </button>
          </div>

          {showOrgForm ? (
            <div className="px-6 py-5">
              <form onSubmit={handleOrgSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name *</label>
                  <input
                    type="text"
                    name="name"
                    required
                    defaultValue={selectedOrg?.name}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Slug *</label>
                  <input
                    type="text"
                    name="slug"
                    required
                    defaultValue={selectedOrg?.slug}
                    pattern="[a-z0-9_-]+"
                    title="Lowercase letters, numbers, hyphens, and underscores only"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">Lowercase letters, numbers, hyphens, and underscores only</p>
                </div>

                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="is_active"
                      value="true"
                      defaultChecked={selectedOrg?.is_active ?? true}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Active</span>
                  </label>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowOrgForm(false)
                      setSelectedOrg(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createOrgMutation.isPending || updateOrgMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
                  >
                    {selectedOrg ? 'Update' : 'Create'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div className="px-6 py-5">
              {organizations && organizations.length > 0 ? (
                <div className="space-y-3">
                  {organizations.map((org) => (
                    <div
                      key={org.id}
                      className="border border-gray-200 rounded-lg p-4"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-sm font-medium text-gray-900">{org.name}</h4>
                          <p className="text-sm text-gray-500 mt-1">Slug: {org.slug}</p>
                          <div className="flex items-center gap-2 mt-2">
                            {org.is_active ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                                Active
                              </span>
                            ) : (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                                Inactive
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              {users?.filter(u => u.org_id === org.id).length || 0} users
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            setSelectedOrg(org)
                            setShowOrgForm(true)
                          }}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No organizations found
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* User-Org Associations Tab */}
      {activeTab === 'associations' && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-5 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">User-Organization Associations</h2>
            <p className="mt-1 text-sm text-gray-500">
              Assign users to organizations
            </p>
          </div>

          <div className="px-6 py-5">
            <button
              onClick={() => setShowOrgAssignment(true)}
              className="mb-4 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm font-medium"
            >
              Assign User to Organization
            </button>

            <div className="space-y-4">
              {users?.map((user) => {
                const userOrg = user.org_id ? organizations?.find(o => o.id === user.org_id) : null
                return (
                  <div key={user.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {user.full_name || user.username}
                        </h4>
                        <p className="text-sm text-gray-500 mt-1">{user.email}</p>
                        <div className="mt-2">
                          {userOrg ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {userOrg.name}
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                              No Organization
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setSelectedUser(user)
                            setShowOrgAssignment(true)
                          }}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          {userOrg ? 'Change' : 'Assign'}
                        </button>
                        {userOrg && (
                          <button
                            onClick={() => {
                              if (confirm(`Remove ${user.full_name || user.username} from ${userOrg.name}?`)) {
                                removeOrgMutation.mutate({
                                  userId: user.id,
                                  orgId: user.org_id!,
                                })
                              }
                            }}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Role Assignment Modal */}
      {showRoleAssignment && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Manage Roles for {selectedUser.full_name || selectedUser.username}
              </h3>

              {/* Current Roles */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Current Roles</h4>
                {userRoles && userRoles.length > 0 ? (
                  <div className="space-y-2">
                    {userRoles.map((userRole) => (
                      <div
                        key={userRole.id}
                        className="flex items-center justify-between border border-gray-200 rounded-lg p-3"
                      >
                        <div>
                          <span className="text-sm font-medium text-gray-900">
                            {userRole.role.name}
                          </span>
                          {userRole.role.description && (
                            <p className="text-xs text-gray-500 mt-1">
                              {userRole.role.description}
                            </p>
                          )}
                        </div>
                        <button
                          onClick={() => {
                            if (confirm(`Remove ${userRole.role.name} role?`)) {
                              removeRoleMutation.mutate({
                                userId: selectedUser.id,
                                roleId: userRole.role_id,
                              })
                            }
                          }}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No roles assigned</p>
                )}
              </div>

              {/* Assign New Role */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Assign New Role</h4>
                <div className="space-y-2">
                  {roles?.filter(
                    (role) => !userRoles?.some((ur) => ur.role_id === role.id)
                  ).map((role) => (
                    <div
                      key={role.id}
                      className="flex items-center justify-between border border-gray-200 rounded-lg p-3"
                    >
                      <div>
                        <span className="text-sm font-medium text-gray-900">
                          {role.name}
                        </span>
                        {role.description && (
                          <p className="text-xs text-gray-500 mt-1">
                            {role.description}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          assignRoleMutation.mutate({
                            userId: selectedUser.id,
                            roleId: role.id,
                          })
                        }}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        Assign
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={() => {
                    setShowRoleAssignment(false)
                    setSelectedUser(null)
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Organization Assignment Modal */}
      {showOrgAssignment && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {selectedUser ? `Assign ${selectedUser.full_name || selectedUser.username} to Organization` : 'Assign User to Organization'}
              </h3>

              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  const formData = new FormData(e.currentTarget)
                  const userId = formData.get('user_id') as string
                  const orgId = formData.get('org_id') as string
                  assignOrgMutation.mutate({ userId, orgId })
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium text-gray-700">User *</label>
                  <select
                    name="user_id"
                    required
                    defaultValue={selectedUser?.id || ''}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="">Select user</option>
                    {users?.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.full_name || user.username} ({user.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Organization *</label>
                  <select
                    name="org_id"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  >
                    <option value="">Select organization</option>
                    {organizations?.map((org) => (
                      <option key={org.id} value={org.id}>{org.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setShowOrgAssignment(false)
                      setSelectedUser(null)
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={assignOrgMutation.isPending}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
                  >
                    Assign
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

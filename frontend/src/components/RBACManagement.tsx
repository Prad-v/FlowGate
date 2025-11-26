/** RBAC Management Component */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { rbacApi, Role, Permission, UserRole } from '../services/api'

interface RBACManagementProps {
  userId?: string
}

export default function RBACManagement({ userId }: RBACManagementProps) {
  const queryClient = useQueryClient()
  const [activeView, setActiveView] = useState<'roles' | 'permissions' | 'users'>('roles')
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const { data: roles, isLoading: rolesLoading } = useQuery({
    queryKey: ['rbac-roles'],
    queryFn: () => rbacApi.getRoles(),
  })

  const { data: permissions, isLoading: permissionsLoading } = useQuery({
    queryKey: ['rbac-permissions'],
    queryFn: () => rbacApi.getPermissions(),
  })

  const { data: userRoles, isLoading: userRolesLoading } = useQuery({
    queryKey: ['rbac-user-roles', userId],
    queryFn: () => userId ? rbacApi.getUserRoles(userId) : Promise.resolve([]),
    enabled: !!userId && activeView === 'users',
  })

  const removeRoleMutation = useMutation({
    mutationFn: ({ userId, roleId }: { userId: string; roleId: string }) =>
      rbacApi.removeRole(userId, roleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rbac-user-roles'] })
      setMessage('Role removed successfully')
      setTimeout(() => setMessage(null), 3000)
    },
    onError: (error: any) => {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`)
      setTimeout(() => setMessage(null), 5000)
    },
  })

  if (rolesLoading || permissionsLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500">Loading RBAC data...</div>
      </div>
    )
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-6 py-5 border-b border-gray-200">
        <h2 className="text-lg font-medium text-gray-900">Role-Based Access Control</h2>
        <p className="mt-1 text-sm text-gray-500">
          Manage roles, permissions, and user assignments
        </p>
      </div>

      {message && (
        <div className={`mx-6 mt-4 rounded-md p-4 ${
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
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
          <button
            onClick={() => setActiveView('roles')}
            className={`${
              activeView === 'roles'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Roles
          </button>
          <button
            onClick={() => setActiveView('permissions')}
            className={`${
              activeView === 'permissions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            Permissions
          </button>
          {userId && (
            <button
              onClick={() => setActiveView('users')}
              className={`${
                activeView === 'users'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
            >
              User Roles
            </button>
          )}
        </nav>
      </div>

      <div className="px-6 py-5">
        {/* Roles View */}
        {activeView === 'roles' && (
          <div>
            <div className="mb-4">
              <h3 className="text-base font-medium text-gray-900">System Roles</h3>
              <p className="text-sm text-gray-500 mt-1">
                Predefined roles with specific permissions
              </p>
            </div>
            <div className="space-y-3">
              {roles?.map((role) => (
                <div
                  key={role.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 cursor-pointer"
                  onClick={() => setSelectedRole(role)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{role.name}</h4>
                      {role.description && (
                        <p className="text-sm text-gray-500 mt-1">{role.description}</p>
                      )}
                      {role.is_system_role && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mt-2">
                          System Role
                        </span>
                      )}
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedRole(role)
                      }}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Permissions View */}
        {activeView === 'permissions' && (
          <div>
            <div className="mb-4">
              <h3 className="text-base font-medium text-gray-900">Permissions</h3>
              <p className="text-sm text-gray-500 mt-1">
                All available permissions in the system
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Permission
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Resource
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {permissions?.map((permission) => (
                    <tr key={permission.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {permission.name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {permission.resource_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {permission.action}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {permission.description || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* User Roles View */}
        {activeView === 'users' && userId && (
          <div>
            <div className="mb-4">
              <h3 className="text-base font-medium text-gray-900">User Roles</h3>
              <p className="text-sm text-gray-500 mt-1">
                Roles assigned to this user
              </p>
            </div>
            {userRolesLoading ? (
              <div className="text-center py-8 text-gray-500">Loading...</div>
            ) : userRoles && userRoles.length > 0 ? (
              <div className="space-y-3">
                {userRoles.map((userRole) => (
                  <div
                    key={userRole.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-sm font-medium text-gray-900">
                          {userRole.role.name}
                        </h4>
                        {userRole.role.description && (
                          <p className="text-sm text-gray-500 mt-1">
                            {userRole.role.description}
                          </p>
                        )}
                        {userRole.org_id && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 mt-2">
                            Org-scoped
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`Remove ${userRole.role.name} role from this user?`)) {
                            removeRoleMutation.mutate({
                              userId,
                              roleId: userRole.role_id,
                            })
                          }
                        }}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No roles assigned to this user
              </div>
            )}
          </div>
        )}
      </div>

      {/* Role Details Modal */}
      {selectedRole && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {selectedRole.name}
              </h3>
              {selectedRole.description && (
                <p className="text-sm text-gray-500 mb-4">{selectedRole.description}</p>
              )}
              <div className="flex justify-end">
                <button
                  onClick={() => setSelectedRole(null)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


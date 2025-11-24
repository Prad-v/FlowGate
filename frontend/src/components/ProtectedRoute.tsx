/** Protected route component that requires authentication */

import { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
  requireRole?: string
  requirePermission?: string
}

export default function ProtectedRoute({ 
  children, 
  requireRole, 
  requirePermission 
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    // Redirect to login with return URL
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check role requirement
  if (requireRole && user) {
    // This would need to be implemented with RBAC API
    // For now, just check is_superuser for super_admin role
    if (requireRole === 'super_admin' && !user.is_superuser) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">Access Denied</h2>
            <p className="mt-2 text-gray-600">You don't have permission to access this page.</p>
          </div>
        </div>
      )
    }
  }

  // Check permission requirement
  if (requirePermission && user) {
    // This would need to be implemented with RBAC API
    // For now, just allow access
  }

  return <>{children}</>
}


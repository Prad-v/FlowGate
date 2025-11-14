import React from 'react'

interface AgentStatusBadgeProps {
  status: 'healthy' | 'warning' | 'unhealthy' | 'offline' | 'online' | 'unknown' | 'registered' | 'active' | 'inactive' | 'error'
}

export default function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'active':
        return 'bg-green-100 text-green-800'
      case 'warning':
        return 'bg-yellow-100 text-yellow-800'
      case 'unhealthy':
      case 'error':
        return 'bg-red-100 text-red-800'
      case 'offline':
      case 'inactive':
      case 'unknown':
        return 'bg-gray-100 text-gray-800'
      case 'registered':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'healthy':
        return 'Healthy'
      case 'warning':
        return 'Warning'
      case 'unhealthy':
        return 'Unhealthy'
      case 'offline':
        return 'Offline'
      case 'online':
        return 'Online'
      case 'registered':
        return 'Registered'
      case 'active':
        return 'Active'
      case 'inactive':
        return 'Inactive'
      case 'error':
        return 'Error'
      case 'unknown':
      default:
        return 'Unknown'
    }
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()}`}
    >
      {getStatusText()}
    </span>
  )
}


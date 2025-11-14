import React from 'react'
import { AgentHealth } from '../services/api'

interface HealthIndicatorProps {
  health: AgentHealth
}

export default function HealthIndicator({ health }: HealthIndicatorProps) {
  const getHealthColor = () => {
    switch (health.status) {
      case 'healthy':
        return 'bg-green-500'
      case 'warning':
        return 'bg-yellow-500'
      case 'unhealthy':
        return 'bg-red-500'
      case 'offline':
      default:
        return 'bg-gray-500'
    }
  }

  const formatUptime = (seconds?: number) => {
    if (!seconds) return 'N/A'
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) return `${days}d ${hours}h`
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  const formatLastSeen = (seconds?: number) => {
    if (!seconds && seconds !== 0) return 'Never'
    if (seconds < 60) return `${seconds}s ago`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    return `${Math.floor(seconds / 86400)}d ago`
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center space-x-2">
        <div className={`w-3 h-3 rounded-full ${getHealthColor()}`} />
        <span className="text-sm font-medium text-gray-900">
          {health.status.charAt(0).toUpperCase() + health.status.slice(1)}
        </span>
        <span className="text-sm text-gray-500">
          (Score: {health.health_score}/100)
        </span>
      </div>
      <div className="text-xs text-gray-600 space-y-1">
        <div>Last seen: {formatLastSeen(health.seconds_since_last_seen)}</div>
        {health.uptime_seconds && (
          <div>Uptime: {formatUptime(health.uptime_seconds)}</div>
        )}
      </div>
    </div>
  )
}


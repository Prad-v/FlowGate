import React from 'react'
import { ConnectionSettingsHashes, ConnectionSettingInfo } from '../services/api'

interface ConnectionSettingsHashesDisplayProps {
  connectionSettingsHashes?: ConnectionSettingsHashes
}

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'APPLIED':
      return 'bg-green-100 text-green-800'
    case 'APPLYING':
      return 'bg-yellow-100 text-yellow-800'
    case 'FAILED':
      return 'bg-red-100 text-red-800'
    case 'UNSET':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

function ConnectionSettingRow({ label, setting }: { label: string; setting: ConnectionSettingInfo | null | undefined }) {
  if (!setting) {
    return (
      <tr>
        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 capitalize">
          {label}
        </td>
        <td colSpan={4} className="px-4 py-3 text-sm text-gray-500">
          Not configured
        </td>
      </tr>
    )
  }

  return (
    <tr>
      <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 capitalize">
        {label}
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(setting.status)}`}>
          {setting.status}
        </span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 font-mono text-xs">
        {setting.settings_hash ? setting.settings_hash.substring(0, 16) + '...' : 'N/A'}
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
        {setting.applied_at ? new Date(setting.applied_at).toLocaleString() : 'N/A'}
      </td>
      <td className="px-4 py-3 text-sm text-red-600">
        {setting.error_message || '-'}
      </td>
    </tr>
  )
}

export default function ConnectionSettingsHashesDisplay({ connectionSettingsHashes }: ConnectionSettingsHashesDisplayProps) {
  if (!connectionSettingsHashes) {
    return (
      <div className="text-sm text-gray-500">No connection settings available</div>
    )
  }

  const hasAnySettings = connectionSettingsHashes.own_metrics || connectionSettingsHashes.own_logs || connectionSettingsHashes.own_traces

  if (!hasAnySettings) {
    return (
      <div className="text-sm text-gray-500">No connection settings configured</div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Connection Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Settings Hash
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Applied At
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Error Message
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          <ConnectionSettingRow label="Own Metrics" setting={connectionSettingsHashes.own_metrics} />
          <ConnectionSettingRow label="Own Logs" setting={connectionSettingsHashes.own_logs} />
          <ConnectionSettingRow label="Own Traces" setting={connectionSettingsHashes.own_traces} />
        </tbody>
      </table>
    </div>
  )
}


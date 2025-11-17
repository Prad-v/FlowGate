import React from 'react'
import { PackageStatus } from '../services/api'

interface PackageStatusesDisplayProps {
  packageStatuses?: PackageStatus[]
}

function getStatusBadgeColor(status: string) {
  switch (status) {
    case 'installed':
      return 'bg-green-100 text-green-800'
    case 'installing':
      return 'bg-yellow-100 text-yellow-800'
    case 'failed':
      return 'bg-red-100 text-red-800'
    case 'uninstalled':
      return 'bg-gray-100 text-gray-800'
    default:
      return 'bg-gray-100 text-gray-800'
  }
}

export default function PackageStatusesDisplay({ packageStatuses }: PackageStatusesDisplayProps) {
  if (!packageStatuses || packageStatuses.length === 0) {
    return (
      <div className="text-sm text-gray-500">No packages installed</div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Package Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Version
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Type
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Installed At
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Error Message
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {packageStatuses.map((pkg, idx) => (
            <tr key={idx} className="hover:bg-gray-50">
              <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                {pkg.package_name}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {pkg.package_version || 'N/A'}
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 capitalize">
                {pkg.package_type}
              </td>
              <td className="px-4 py-3 whitespace-nowrap">
                <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeColor(pkg.status)}`}>
                  {pkg.status}
                </span>
              </td>
              <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                {pkg.installed_at ? new Date(pkg.installed_at).toLocaleString() : 'N/A'}
              </td>
              <td className="px-4 py-3 text-sm text-red-600">
                {pkg.error_message || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


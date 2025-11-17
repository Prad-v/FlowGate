import React from 'react'
import { AgentDescription } from '../services/api'

interface AgentDescriptionDisplayProps {
  agentDescription?: AgentDescription
}

export default function AgentDescriptionDisplay({ agentDescription }: AgentDescriptionDisplayProps) {
  if (!agentDescription) {
    return (
      <div className="text-sm text-gray-500">No agent description available</div>
    )
  }

  const { identifiers, os_runtime, build_info, identifying_attributes, non_identifying_attributes } = agentDescription

  return (
    <div className="space-y-6">
      {/* Identifiers Section */}
      {identifiers && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Identifiers</h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {identifiers.instance_uid && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Instance UID</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{identifiers.instance_uid}</dd>
              </div>
            )}
            {identifiers.agent_type && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Agent Type</dt>
                <dd className="mt-1 text-sm text-gray-900">{identifiers.agent_type}</dd>
              </div>
            )}
            {identifiers.agent_version && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Agent Version</dt>
                <dd className="mt-1 text-sm text-gray-900">{identifiers.agent_version}</dd>
              </div>
            )}
            {identifiers.agent_id && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Agent ID</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono">{identifiers.agent_id}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* OS/Runtime Information Section */}
      {os_runtime && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">OS / Runtime Information</h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {os_runtime.operating_system && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Operating System</dt>
                <dd className="mt-1 text-sm text-gray-900">{os_runtime.operating_system}</dd>
              </div>
            )}
            {os_runtime.architecture && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Architecture</dt>
                <dd className="mt-1 text-sm text-gray-900">{os_runtime.architecture}</dd>
              </div>
            )}
            {os_runtime.labels && Object.keys(os_runtime.labels).length > 0 && (
              <div className="col-span-2">
                <dt className="text-xs font-medium text-gray-500 mb-2">Labels</dt>
                <dd className="mt-1">
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(os_runtime.labels).map(([key, value]) => (
                      <span
                        key={key}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                </dd>
              </div>
            )}
            {os_runtime.extensions && os_runtime.extensions.length > 0 && (
              <div className="col-span-2">
                <dt className="text-xs font-medium text-gray-500 mb-2">Extensions</dt>
                <dd className="mt-1">
                  <div className="flex flex-wrap gap-2">
                    {os_runtime.extensions.map((ext, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {ext}
                      </span>
                    ))}
                  </div>
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Build Info Section */}
      {build_info && (
        <div>
          <h3 className="text-sm font-medium text-gray-900 mb-3">Build Information</h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {build_info['build.git.sha'] && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Git SHA</dt>
                <dd className="mt-1 text-sm text-gray-900 font-mono text-xs">{build_info['build.git.sha']}</dd>
              </div>
            )}
            {build_info['build.timestamp'] && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Build Timestamp</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {new Date(build_info['build.timestamp']).toLocaleString()}
                </dd>
              </div>
            )}
            {build_info['distro.name'] && (
              <div>
                <dt className="text-xs font-medium text-gray-500">Distribution</dt>
                <dd className="mt-1 text-sm text-gray-900">{build_info['distro.name']}</dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Raw Attributes (if available and identifiers/os_runtime/build_info are not) */}
      {(!identifiers && !os_runtime && !build_info) && (
        <>
          {identifying_attributes && identifying_attributes.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Identifying Attributes</h3>
              <div className="bg-gray-50 rounded-md p-3">
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {identifying_attributes.map((attr, idx) => (
                    <div key={idx}>
                      <dt className="text-xs font-medium text-gray-600">{attr.key}</dt>
                      <dd className="text-xs text-gray-900 font-mono">{attr.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}
          {non_identifying_attributes && non_identifying_attributes.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Non-Identifying Attributes</h3>
              <div className="bg-gray-50 rounded-md p-3">
                <dl className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {non_identifying_attributes.map((attr, idx) => (
                    <div key={idx}>
                      <dt className="text-xs font-medium text-gray-600">{attr.key}</dt>
                      <dd className="text-xs text-gray-900 font-mono">{attr.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}


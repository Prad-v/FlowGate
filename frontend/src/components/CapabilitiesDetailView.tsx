import React, { useState } from 'react';
import { CAPABILITY_METADATA, CAPABILITY_CATEGORIES } from '../config/capabilities';

interface CapabilitiesDetailViewProps {
  bitField: number | null | undefined;
  decoded: string[] | null | undefined;
  label?: string;
  className?: string;
  agentData?: {
    instance_id?: string;
    agent_version?: any;
    health?: any;
    opamp_effective_config_hash?: string | null;
    opamp_remote_config_status?: string | null;
    opamp_remote_config_hash?: string | null;
    opamp_last_sequence_num?: number | null;
    identifying_attributes?: any;
    available_components?: any;
  };
}

export const CapabilitiesDetailView: React.FC<CapabilitiesDetailViewProps> = ({
  bitField,
  decoded,
  label = 'Capabilities',
  className = '',
  agentData,
}) => {
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Reporting', 'Configuration', 'Connection', 'Lifecycle']));
  const [expandedCapabilities, setExpandedCapabilities] = useState<Set<string>>(new Set());

  if (bitField === null || bitField === undefined) {
    return (
      <div className={className}>
        <div className="text-sm font-medium text-gray-700 mb-1">{label}</div>
        <div className="text-sm text-gray-500">Not available</div>
      </div>
    );
  }

  const enabledCapabilities = new Set(decoded || []);
  const hexValue = `0x${bitField.toString(16).toUpperCase()}`;

  const toggleCategory = (categoryName: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryName)) {
      newExpanded.delete(categoryName);
    } else {
      newExpanded.add(categoryName);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleCapability = (capabilityName: string) => {
    const newExpanded = new Set(expandedCapabilities);
    if (newExpanded.has(capabilityName)) {
      newExpanded.delete(capabilityName);
    } else {
      newExpanded.add(capabilityName);
    }
    setExpandedCapabilities(newExpanded);
  };

  const getCategoryStats = (categoryCapabilities: readonly string[]) => {
    const enabled = categoryCapabilities.filter(cap => enabledCapabilities.has(cap)).length;
    const total = categoryCapabilities.length;
    return { enabled, total };
  };

  const renderCapabilityData = (capabilityName: string, isEnabled: boolean) => {
    if (!isEnabled || !agentData) {
      return (
        <div className="text-xs text-gray-500 italic">
          {isEnabled ? 'Data not available' : 'Capability not enabled'}
        </div>
      );
    }

    switch (capabilityName) {
      case 'ReportsStatus':
        return (
          <div className="space-y-2 text-sm">
            {agentData.instance_id && (
              <div>
                <span className="font-medium text-gray-700">Instance ID:</span>
                <span className="ml-2 font-mono text-xs text-gray-600">{agentData.instance_id}</span>
              </div>
            )}
            {agentData.agent_version && (
              <div>
                <span className="font-medium text-gray-700">Agent Version:</span>
                <span className="ml-2 text-gray-600">
                  {agentData.agent_version.agent_version || 'N/A'}
                </span>
              </div>
            )}
            {agentData.identifying_attributes && Object.keys(agentData.identifying_attributes).length > 0 && (
              <div>
                <span className="font-medium text-gray-700">Attributes:</span>
                <div className="ml-2 mt-1 space-y-1">
                  {Object.entries(agentData.identifying_attributes).map(([key, value]) => (
                    <div key={key} className="text-xs">
                      <span className="text-gray-600">{key}:</span>
                      <span className="ml-1 text-gray-800">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 'ReportsEffectiveConfig':
        return (
          <div className="space-y-2 text-sm">
            {agentData.opamp_effective_config_hash ? (
              <div>
                <span className="font-medium text-gray-700">Config Hash:</span>
                <span className="ml-2 font-mono text-xs text-gray-600">{agentData.opamp_effective_config_hash}</span>
              </div>
            ) : (
              <div className="text-xs text-gray-500">No effective config hash available</div>
            )}
          </div>
        );

      case 'ReportsHealth':
        return (
          <div className="space-y-2 text-sm">
            {agentData.health && (agentData.health.healthy !== null && agentData.health.healthy !== undefined) ? (
              <div>
                <span className="font-medium text-gray-700">Health Status:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs ${
                  agentData.health.healthy === true ? 'bg-green-100 text-green-800' : 
                  agentData.health.healthy === false ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {agentData.health.healthy === true ? 'Healthy' : 
                   agentData.health.healthy === false ? 'Unhealthy' : 
                   'Unknown'}
                </span>
                {(agentData.health.latest_error || agentData.health.last_error) && (
                  <div className="mt-2 text-xs text-red-600">
                    Error: {agentData.health.latest_error || agentData.health.last_error}
                  </div>
                )}
                {agentData.health.start_time_unix_nano && (
                  <div className="mt-1 text-xs text-gray-500">
                    Started: {new Date(Number(agentData.health.start_time_unix_nano) / 1000000).toLocaleString()}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-1">
                <div className="text-xs text-gray-500 italic">
                  Health data not reported by agent
                </div>
                <div className="text-xs text-gray-400">
                  The agent has ReportsHealth capability enabled but is not sending health messages.
                  This may indicate the collector is not fully started or health reporting is not configured.
                </div>
              </div>
            )}
          </div>
        );

      case 'ReportsRemoteConfig':
        return (
          <div className="space-y-2 text-sm">
            {agentData.opamp_remote_config_status ? (
              <div>
                <span className="font-medium text-gray-700">Status:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs ${
                  agentData.opamp_remote_config_status === 'APPLIED' ? 'bg-green-100 text-green-800' :
                  agentData.opamp_remote_config_status === 'FAILED' ? 'bg-red-100 text-red-800' :
                  agentData.opamp_remote_config_status === 'APPLYING' ? 'bg-blue-100 text-blue-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {agentData.opamp_remote_config_status}
                </span>
                {agentData.opamp_remote_config_status === 'UNSET' && (
                  <div className="mt-1 text-xs text-gray-500 italic">
                    No remote config has been sent to this agent yet
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-gray-500">Remote config status not available</div>
            )}
            {agentData.opamp_remote_config_hash && (
              <div>
                <span className="font-medium text-gray-700">Config Hash:</span>
                <span className="ml-2 font-mono text-xs text-gray-600">{agentData.opamp_remote_config_hash}</span>
              </div>
            )}
          </div>
        );

      case 'ReportsHeartbeat':
        return (
          <div className="space-y-2 text-sm">
            {agentData.opamp_last_sequence_num !== null && agentData.opamp_last_sequence_num !== undefined && (
              <div>
                <span className="font-medium text-gray-700">Last Sequence:</span>
                <span className="ml-2 font-mono text-xs text-gray-600">{agentData.opamp_last_sequence_num}</span>
              </div>
            )}
          </div>
        );

      case 'ReportsAvailableComponents':
        return (
          <div className="space-y-2 text-sm">
            {agentData.available_components ? (
              <div>
                <span className="font-medium text-gray-700">Components:</span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {Array.isArray(agentData.available_components) ? (
                    agentData.available_components.map((comp: string, idx: number) => (
                      <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                        {comp}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-500">Component data format not recognized</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-xs text-gray-500">Component data not available</div>
            )}
          </div>
        );

      case 'AcceptsRemoteConfig':
        return (
          <div className="space-y-2 text-sm">
            {agentData.opamp_remote_config_status && (
              <div>
                <span className="font-medium text-gray-700">Remote Config:</span>
                <span className={`ml-2 px-2 py-1 rounded text-xs ${
                  agentData.opamp_remote_config_status === 'APPLIED' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {agentData.opamp_remote_config_status === 'APPLIED' ? 'Accepted' : 'Not Applied'}
                </span>
              </div>
            )}
          </div>
        );

      case 'AcceptsOpAMPConnectionSettings':
        return (
          <div className="space-y-2 text-sm">
            <div className="text-xs text-gray-500">
              Connection settings managed via OpAMP
            </div>
          </div>
        );

      case 'AcceptsRestartCommand':
        return (
          <div className="space-y-2 text-sm">
            <div className="text-xs text-gray-500">
              Agent supports remote restart commands
            </div>
          </div>
        );

      case 'ReportsOwnTraces':
      case 'ReportsOwnMetrics':
      case 'ReportsOwnLogs':
        return (
          <div className="space-y-2 text-sm">
            <div className="text-xs text-gray-500">
              Telemetry data available via connection settings
            </div>
          </div>
        );

      default:
        return (
          <div className="text-xs text-gray-500">
            Data display not implemented for this capability
          </div>
        );
    }
  };

  return (
    <div className={className}>
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="text-sm font-medium text-gray-700">{label}</div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-gray-600">Bit-field:</span>
            <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{hexValue}</span>
            <span className="text-xs text-gray-500">({bitField})</span>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {CAPABILITY_CATEGORIES.map((category) => {
          const stats = getCategoryStats(category.capabilities);
          const isExpanded = expandedCategories.has(category.name);
          
          return (
            <div key={category.name} className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                onClick={() => toggleCategory(category.name)}
                className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <span className="text-lg">{category.icon}</span>
                  <span className="font-medium text-gray-900">{category.name}</span>
                  <span className="text-xs text-gray-500">
                    ({stats.enabled}/{stats.total} enabled)
                  </span>
                </div>
                <svg
                  className={`w-5 h-5 text-gray-500 transition-transform ${isExpanded ? 'transform rotate-180' : ''}`}
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {isExpanded && (
                <div className="p-4 bg-white">
                  <div className="grid grid-cols-1 gap-3">
                    {category.capabilities.map((capName) => {
                      const capability = CAPABILITY_METADATA[capName];
                      if (!capability) return null;

                      const isEnabled = enabledCapabilities.has(capName);
                      const isCapabilityExpanded = expandedCapabilities.has(capName);

                      return (
                        <div
                          key={capName}
                          className={`border rounded-lg overflow-hidden transition-colors ${
                            isEnabled
                              ? 'border-green-200 bg-green-50'
                              : 'border-gray-200 bg-gray-50'
                          }`}
                        >
                          <button
                            onClick={() => toggleCapability(capName)}
                            className="w-full px-4 py-3 flex items-center justify-between hover:bg-opacity-80 transition-colors"
                          >
                            <div className="flex items-center gap-3 flex-1">
                              <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${
                                isEnabled ? 'bg-green-500' : 'bg-gray-400'
                              }`}>
                                {isEnabled ? (
                                  <svg className="w-4 h-4 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M5 13l4 4L19 7" />
                                  </svg>
                                ) : (
                                  <svg className="w-4 h-4 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
                                    <path d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                )}
                              </div>
                              <div className="flex-1 text-left">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-900">{capability.name}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded ${
                                    isEnabled
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-gray-200 text-gray-600'
                                  }`}>
                                    {isEnabled ? 'Enabled' : 'Disabled'}
                                  </span>
                                  <span className="text-xs font-mono text-gray-500">
                                    Bit {capability.bitPosition}: {capability.hexValue}
                                  </span>
                                  {/* Help icon with tooltip */}
                                  <div className="group relative">
                                    <svg
                                      className="w-4 h-4 text-gray-400 hover:text-gray-600 cursor-help"
                                      fill="none"
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      strokeWidth="2"
                                      viewBox="0 0 24 24"
                                      stroke="currentColor"
                                    >
                                      <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <div className="absolute left-0 bottom-full mb-2 w-96 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 pointer-events-none">
                                      <div className="space-y-3">
                                        <div>
                                          <strong className="text-white">What it is:</strong>
                                          <p className="mt-1 text-gray-300 leading-relaxed">{capability.description.whatItIs}</p>
                                        </div>
                                        <div>
                                          <strong className="text-white">Architectural impact:</strong>
                                          <p className="mt-1 text-gray-300 leading-relaxed">{capability.description.architecturalImpact}</p>
                                        </div>
                                        <div>
                                          <strong className="text-white">What it buys you:</strong>
                                          <p className="mt-1 text-gray-300 leading-relaxed">{capability.description.whatItBuysYou}</p>
                                        </div>
                                      </div>
                                      <div className="absolute left-4 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                            <svg
                              className={`w-5 h-5 text-gray-500 transition-transform flex-shrink-0 ${
                                isCapabilityExpanded ? 'transform rotate-180' : ''
                              }`}
                              fill="none"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path d="M19 9l-7 7-7-7" />
                            </svg>
                          </button>

                          {isCapabilityExpanded && (
                            <div className="px-4 pb-4 pt-2 border-t border-gray-200 bg-white">
                              {renderCapabilityData(capName, isEnabled)}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

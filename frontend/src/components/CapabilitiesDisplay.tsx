import React from 'react';
import { CapabilitiesDetailView } from './CapabilitiesDetailView';

interface CapabilitiesDisplayProps {
  bitField: number | null | undefined;
  decoded: string[] | null | undefined;
  label?: string;
  className?: string;
  detailed?: boolean;
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

export const CapabilitiesDisplay: React.FC<CapabilitiesDisplayProps> = ({
  bitField,
  decoded,
  label = 'Capabilities',
  className = '',
  detailed = false,
  agentData,
}) => {
  // Use detailed view if requested
  if (detailed) {
    return (
      <CapabilitiesDetailView
        bitField={bitField}
        decoded={decoded}
        label={label}
        className={className}
        agentData={agentData}
      />
    );
  }

  if (bitField === null || bitField === undefined) {
    return (
      <div className={className}>
        <div className="text-sm font-medium text-gray-700 mb-1">{label}</div>
        <div className="text-sm text-gray-500">Not available</div>
      </div>
    );
  }

  const hexValue = `0x${bitField.toString(16).toUpperCase()}`;
  const capabilities = decoded || [];

  return (
    <div className={className}>
      <div className="text-sm font-medium text-gray-700 mb-2">{label}</div>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-gray-600">Bit-field:</span>
          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{hexValue}</span>
          <span className="text-xs text-gray-500">({bitField})</span>
        </div>
        {capabilities.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {capabilities.map((cap, index) => (
              <span
                key={index}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200"
                title={`Capability: ${cap}`}
              >
                {cap}
              </span>
            ))}
          </div>
        ) : (
          <div className="text-xs text-gray-500">No capabilities enabled</div>
        )}
      </div>
    </div>
  );
};


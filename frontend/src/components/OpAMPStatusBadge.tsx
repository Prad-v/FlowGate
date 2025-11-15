import React from 'react';

export type OpAMPConnectionStatus = 'connected' | 'disconnected' | 'failed' | 'never_connected' | null | undefined;

interface OpAMPStatusBadgeProps {
  status: OpAMPConnectionStatus;
  className?: string;
}

export const OpAMPStatusBadge: React.FC<OpAMPStatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          label: 'Connected',
          color: 'bg-green-100 text-green-800 border-green-200',
          dot: 'bg-green-500',
        };
      case 'disconnected':
        return {
          label: 'Disconnected',
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          dot: 'bg-yellow-500',
        };
      case 'failed':
        return {
          label: 'Failed',
          color: 'bg-red-100 text-red-800 border-red-200',
          dot: 'bg-red-500',
        };
      case 'never_connected':
        return {
          label: 'Never Connected',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          dot: 'bg-gray-400',
        };
      default:
        return {
          label: 'Unknown',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          dot: 'bg-gray-400',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.color} ${className}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
};


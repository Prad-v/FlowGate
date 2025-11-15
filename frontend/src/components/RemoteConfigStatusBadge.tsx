import React from 'react';

export type RemoteConfigStatus = 'UNSET' | 'APPLIED' | 'APPLYING' | 'FAILED' | null | undefined;

interface RemoteConfigStatusBadgeProps {
  status: RemoteConfigStatus;
  className?: string;
}

export const RemoteConfigStatusBadge: React.FC<RemoteConfigStatusBadgeProps> = ({ status, className = '' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'APPLIED':
        return {
          label: 'Applied',
          color: 'bg-green-100 text-green-800 border-green-200',
          dot: 'bg-green-500',
        };
      case 'APPLYING':
        return {
          label: 'Applying',
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          dot: 'bg-blue-500',
        };
      case 'FAILED':
        return {
          label: 'Failed',
          color: 'bg-red-100 text-red-800 border-red-200',
          dot: 'bg-red-500',
        };
      case 'UNSET':
      default:
        return {
          label: 'Unset',
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


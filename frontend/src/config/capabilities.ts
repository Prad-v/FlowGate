export interface CapabilityInfo {
  name: string;
  bitPosition: number;
  hexValue: string;
  category: 'Reporting' | 'Configuration' | 'Connection' | 'Lifecycle';
  description: {
    whatItIs: string;
    architecturalImpact: string;
    whatItBuysYou: string;
  };
  icon?: string;
}

export const CAPABILITY_METADATA: Record<string, CapabilityInfo> = {
  ReportsStatus: {
    name: 'ReportsStatus',
    bitPosition: 0,
    hexValue: '0x01',
    category: 'Reporting',
    description: {
      whatItIs: 'Baseline capability: the agent must send AgentToServer messages with its core status and description. Includes metadata such as: Agent type and version, OS / platform details, Instance UID, Basic state (running, starting, error modes via package/health fields).',
      architecturalImpact: 'Enables a live inventory of all agents ("what\'s out there?"). Lets the control plane tailor config and packages by: Version, Platform, Environment / labels. Forms the basis of a "Fleet Overview" page: list of collectors, versions, last-seen timestamps.',
      whatItBuysYou: 'Single source of truth for agent inventory. Ability to drive rollouts ("send this config to all 0.102.x Linux collectors in prod").'
    },
    icon: '📊'
  },
  AcceptsRemoteConfig: {
    name: 'AcceptsRemoteConfig',
    bitPosition: 1,
    hexValue: '0x02',
    category: 'Configuration',
    description: {
      whatItIs: 'Agent is willing to receive ServerToAgent.remote_config and apply it as its configuration source.',
      architecturalImpact: 'Moves config ownership from "YAML baked into DaemonSet/VM" → to "Config as data in the OpAMP control plane." Supervisor pattern: Supervisor receives remote config via OpAMP. Merges it with local/base config. Writes a final collector config file. Starts/reloads the collector process with that file.',
      whatItBuysYou: 'Zero-touch config changes for agents: Change pipelines, receivers, exporters centrally. Avoid SSH / kubectl / baking new images for config-only changes. Enables safe rollout patterns: Blue/green or canary configs per label set. Drag-and-drop UI policies → translated into collector config.'
    },
    icon: '⚙️'
  },
  ReportsEffectiveConfig: {
    name: 'ReportsEffectiveConfig',
    bitPosition: 2,
    hexValue: '0x04',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent can send its effective configuration (what it\'s actually running with), not just the remote fragment from the server. Effective config = merge of: Local/static config, Remote OpAMP config, Dynamic pieces (env expansion, includes, etc.).',
      architecturalImpact: 'You can see exactly what every agent is running, even if: Different clusters use different Helm values. Local overrides or bootstrap configs exist. Control plane can diff: Desired config (remote) vs Effective config (applied).',
      whatItBuysYou: 'Debug superpower: "Why is this collector still shipping to the old backend?" → inspect effective config. Compliance / audit: "Show me every agent that has sampling disabled" → query against effective configs. Drift detection: Detect local changes that conflict with central policy.'
    },
    icon: '📋'
  },
  ReportsOwnTraces: {
    name: 'ReportsOwnTraces',
    bitPosition: 5,
    hexValue: '0x20',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent can emit its own process-level traces to a destination defined via OpAMP ConnectionSettingsOffers.own_traces.',
      architecturalImpact: 'Adds a dedicated telemetry channel for the agent itself, separate from tenant traffic: Example: trace spans around internal pipelines, exporters, and external calls (e.g., target backends, remote endpoints).',
      whatItBuysYou: 'Deep debugging of collector behavior, not just app behavior: Traces showing pipeline latencies, exporter retries, etc. Allows: Centralized tracing of all collectors into a "control-plane observability" backend. Performance baseline per agent version / config.'
    },
    icon: '🔍'
  },
  ReportsOwnMetrics: {
    name: 'ReportsOwnMetrics',
    bitPosition: 6,
    hexValue: '0x40',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent exposes process and internal metrics to a destination the server offers in connection settings (own metrics channel).',
      architecturalImpact: 'Standardized metrics like: CPU, memory, file descriptors. Pipeline metrics: batch sizes, queue length, dropped data, export errors. Sent to a backplane metrics cluster, not mixed with application metrics.',
      whatItBuysYou: 'Fleet-wide SRE view: "Which collectors are CPU bound?" "Where are we dropping logs/metrics/traces?" Enables autoscaling / capacity planning based on real agent metrics, not guesswork.'
    },
    icon: '📈'
  },
  ReportsOwnLogs: {
    name: 'ReportsOwnLogs',
    bitPosition: 7,
    hexValue: '0x80',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent can ship its own logs (supervisor/collector logs) to a log backend defined via OpAMP connection settings.',
      architecturalImpact: 'Unified log channel for: Config errors (invalid pipeline, bad exporter). Network errors to backends. Upgrade / package install logs. Logs are decoupled from the tenant streams, so you have clean platform logs.',
      whatItBuysYou: 'Centralized troubleshooting for the fleet: Search: component=otelcol-supervisor AND level=error. Faster incident response: Correlate "drop in tenant metrics" with logs from the specific collector reporting exporter failures.'
    },
    icon: '📝'
  },
  AcceptsOpAMPConnectionSettings: {
    name: 'AcceptsOpAMPConnectionSettings',
    bitPosition: 8,
    hexValue: '0x100',
    category: 'Connection',
    description: {
      whatItIs: 'Agent is willing to accept connection settings (credentials, endpoints, TLS material, proxy settings) from the server via ConnectionSettingsOffers.',
      architecturalImpact: 'Server can centrally manage: OTLP endpoints (for own telemetry). Credentials (API tokens, mTLS certs). Proxies / egress details. Connection settings can be updated without touching the agent config or image.',
      whatItBuysYou: 'Credential rotation as a control plane action: Rotate tokens/certs at scale without SSH / redeploys. Rapid topology changes: Move from one OTLP backend to another. Route agent telemetry via different gateways based on environment or region.'
    },
    icon: '🔌'
  },
  AcceptsRestartCommand: {
    name: 'AcceptsRestartCommand',
    bitPosition: 10,
    hexValue: '0x400',
    category: 'Lifecycle',
    description: {
      whatItIs: 'Agent supports ServerToAgentCommand with type Restart. Server can ask the agent to restart itself.',
      architecturalImpact: 'Enables remote lifecycle control: OpAMP server as "orchestrator" for restart workflows. Typical otelcol-supervisor path: Supervisor receives restart command over OpAMP. Supervisor stops & restarts collector process. Reports outcome via status / health / package status.',
      whatItBuysYou: 'Operational tools: Roll out a config change → restart all collectors in a canary group. Recover from known bad states by remote restart. Reduces reliance on: Kubernetes/VM automation for restarts in non-K8s environments. Ad-hoc scripting for mass restarts.'
    },
    icon: '🔄'
  },
  ReportsHealth: {
    name: 'ReportsHealth',
    bitPosition: 11,
    hexValue: '0x800',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent reports health state for itself and its components via OpAMP (ComponentHealth, etc.).',
      architecturalImpact: 'Health is not just "process up/down"; it can encode: Degraded (e.g., exporter failing). Partially healthy components (some pipelines OK, others failing). Specific error reason/summary.',
      whatItBuysYou: 'Control-plane health dashboards: "Show me all collectors with unhealthy pipelines" instead of generic pod-level health. SRE workflows: Trigger alerts or automated remediation when an agent\'s health flips from OK → Degraded/Unhealthy. Drive package rollback or config rollback based on fleet health.'
    },
    icon: '💚'
  },
  ReportsRemoteConfig: {
    name: 'ReportsRemoteConfig',
    bitPosition: 12,
    hexValue: '0x1000',
    category: 'Configuration',
    description: {
      whatItIs: 'Agent reports status of the remote config it received and attempted to apply, via remote_config_status.',
      architecturalImpact: 'Feedback loop for config pushes: Was the remote config accepted? Did validation or apply step fail? Was a rollback necessary?',
      whatItBuysYou: 'Safe rollout engine: Server pushes config version N. Agents report remote config status = success/failure. Control plane: Automatically rolls back agents that failed. Marks rollout as green only when success rate passes threshold. Strong auditability: "Which agents successfully applied config_version=2025-11-17.3?"'
    },
    icon: '✅'
  },
  ReportsHeartbeat: {
    name: 'ReportsHeartbeat',
    bitPosition: 13,
    hexValue: '0x2000',
    category: 'Lifecycle',
    description: {
      whatItIs: 'Agent sends lightweight heartbeat messages on a regular cadence, explicitly indicating liveness.',
      architecturalImpact: 'Decouples "I sent some status once" from "I am still alive". Heartbeat payloads are typically small: Instance UID, Timestamp, Optional quick health signal.',
      whatItBuysYou: 'Reliable online/offline view: "Last heartbeat < 60s → Online". Anything older → suspect network or crash. Drives: Control-plane status indicators ("green/red" per agent). Alerting when a whole slice (cluster/region) stops heartbeating.'
    },
    icon: '💓'
  },
  ReportsAvailableComponents: {
    name: 'ReportsAvailableComponents',
    bitPosition: 14,
    hexValue: '0x4000',
    category: 'Reporting',
    description: {
      whatItIs: 'Agent can report a list of components it has or manages: Pipeline components (receivers, processors, exporters). Additional binaries/add-ons or packages.',
      architecturalImpact: 'Enriched inventory that\'s not just "collector vX.Y" but: "Collector v0.139 + these exporters + these processors". Additional add-ons (custom receivers, sidecar tools, etc.)',
      whatItBuysYou: 'Policy control: "Find all agents that don\'t have the filelog receiver" → drive targeted package offers or config changes. Upgrade strategy: Know which capabilities exist before pushing config that requires them.'
    },
    icon: '🧩'
  }
};

export const CAPABILITY_CATEGORIES = [
  {
    name: 'Reporting',
    icon: '📊',
    capabilities: ['ReportsStatus', 'ReportsEffectiveConfig', 'ReportsOwnTraces', 'ReportsOwnMetrics', 'ReportsOwnLogs', 'ReportsHealth', 'ReportsRemoteConfig', 'ReportsHeartbeat', 'ReportsAvailableComponents']
  },
  {
    name: 'Configuration',
    icon: '⚙️',
    capabilities: ['AcceptsRemoteConfig', 'ReportsEffectiveConfig', 'ReportsRemoteConfig']
  },
  {
    name: 'Connection',
    icon: '🔌',
    capabilities: ['AcceptsOpAMPConnectionSettings']
  },
  {
    name: 'Lifecycle',
    icon: '🔄',
    capabilities: ['AcceptsRestartCommand', 'ReportsHealth', 'ReportsHeartbeat']
  }
] as const;


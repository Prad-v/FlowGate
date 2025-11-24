# FlowGate Security Modules Guide

## Overview

FlowGate Security Platform includes 5 AI-powered agents that work together to detect threats, manage access, and automate security responses. This guide explains how each module works and how they integrate.

## Architecture Flow

```
Logs → OTel Collector → Log Transformation → NATS Event Bus
                                                    ↓
                    ┌──────────────────────────────┴──────────────────────────────┐
                    ↓                              ↓                              ↓
            Threat Vector Agent          Identity Governance Agent      Persona Baseline Agent
                    ↓                              ↓                              ↓
            Threat Alerts ───────────→ Correlation & RCA Agent ←────────── Anomalies
                    ↓                              ↓
            SOAR Automation Agent ←────────── Incidents
                    ↓
            Automated Response Actions
```

## Security Modules

### 1. Identity Governance Agent (IGA)

**Purpose**: Manages access requests and detects unauthorized privilege changes.

**How It Works**:
1. **Access Request Evaluation**: When a user requests access to a resource (JITA/JITP), IGA:
   - Queries Neo4j access graph to find user roles and permissions
   - Calculates risk score based on:
     - Number of access paths (more paths = higher risk)
     - Privilege level of user roles
     - Resource sensitivity
     - Requested duration
   - Detects role drift (unexpected role changes)
   - Generates recommendations (auto-approve, require approval, limit duration)

2. **Role Drift Detection**: 
   - Compares current user roles with historical baseline
   - Flags unexpected privilege escalations
   - Alerts when users gain access beyond their normal scope

3. **Entitlement Risk Analysis**:
   - Analyzes all user permissions across resources
   - Identifies over-privileged accounts
   - Suggests permission reductions

**Data Sources**: 
- Identity provider logs (Okta, Azure AD, Keycloak, GCP IAM)
- Access logs from JITA/JITP systems
- Neo4j access graph (users, roles, resources, permissions)

**Key Features**:
- Risk scoring (0.0 to 1.0)
- Role drift alerts
- Access path analysis
- Auto-approval recommendations

---

### 2. Threat Vector Agent (TVA)

**Purpose**: Detects security threats using MITRE ATT&CK framework and behavioral analytics.

**How It Works**:
1. **Log Analysis**: 
   - Subscribes to normalized logs from NATS event bus
   - Analyzes logs from identity, network, endpoint, and application sources
   - Uses ML embeddings to detect anomalies

2. **MITRE ATT&CK Mapping**:
   - Matches log patterns to MITRE ATT&CK techniques
   - Identifies tactics (Initial Access, Execution, Persistence, etc.)
   - Maps to specific techniques (T1003, T1078, etc.)

3. **Anomaly Detection**:
   - Calculates anomaly score using vector similarity
   - Compares current behavior to historical patterns
   - Flags deviations above threshold (default: 0.7)

4. **Threat Alert Creation**:
   - Creates alerts for detected threats
   - Assigns severity (Low, Medium, High, Critical)
   - Links to MITRE techniques
   - Stores confidence and anomaly scores

**Data Sources**:
- Network logs (firewall, proxy, WAF)
- Endpoint logs (servers, workstations, containers)
- Application logs (API gateways, microservices)
- Threat intelligence feeds

**Key Features**:
- MITRE ATT&CK TTP mapping
- Anomaly detection (ML-based)
- Multi-step attack pattern detection
- Threat intelligence integration

---

### 3. Correlation & RCA Agent (CRA)

**Purpose**: Correlates multiple security events and performs root cause analysis.

**How It Works**:
1. **Event Correlation**:
   - Receives threat alerts from TVA
   - Groups related alerts by:
     - Time window (default: 60 minutes)
     - Common entities (users, IPs, resources)
     - MITRE tactics/techniques
   - Builds attack timeline

2. **Incident Creation**:
   - Creates incidents when multiple alerts correlate
   - Determines severity (highest from correlated alerts)
   - Links all related alerts
   - Estimates blast radius (affected resources/users)

3. **Root Cause Analysis**:
   - Analyzes attack timeline
   - Identifies initial entry point
   - Traces attack progression
   - Determines root cause with confidence score

4. **Timeline Reconstruction**:
   - Orders events chronologically
   - Shows attack progression
   - Highlights key events

**Data Sources**:
- Threat alerts from TVA
- Logs from multiple sources
- Neo4j access graph (for blast radius)
- Historical incidents

**Key Features**:
- Cross-log correlation
- Attack timeline reconstruction
- Root cause analysis
- Blast radius estimation

---

### 4. Persona Baseline Agent (PBA)

**Purpose**: Learns normal user and service behavior to detect anomalies.

**How It Works**:
1. **Baseline Learning**:
   - Collects behavior samples for users/services
   - Learns patterns:
     - Login times and frequencies
     - Resource access patterns
     - IP addresses used
     - Actions performed
   - Creates vector embeddings for similarity search
   - Updates baselines continuously

2. **Anomaly Detection**:
   - Compares new activity to baseline
   - Calculates deviation score
   - Flags anomalies above threshold (default: 0.7)
   - Types of anomalies:
     - Unusual time of access
     - New IP address
     - Unusual resource access
     - Unusual action pattern

3. **Baseline Management**:
   - Tracks sample count
   - Marks baselines as active/inactive
   - Updates thresholds based on confidence

**Data Sources**:
- User activity logs
- Service logs
- Access logs
- Application logs

**Key Features**:
- User behavior baselines
- Service behavior baselines
- Anomaly detection via embeddings
- Continuous learning

---

### 5. SOAR Automation Agent (SAA)

**Purpose**: Automates security response actions through playbooks.

**How It Works**:
1. **Playbook Definition**:
   - Playbooks defined in YAML format
   - Trigger conditions (threat alert, incident, access request, anomaly, manual)
   - Actions to execute (notify, block IP, rotate keys, create ticket, etc.)
   - Approval requirements (optional)

2. **Playbook Execution**:
   - Monitors for trigger conditions
   - Evaluates conditions against events
   - Executes actions if conditions match
   - Requires approval if configured
   - Logs all actions taken

3. **Integration Actions**:
   - **Slack**: Send notifications to channels
   - **JIRA**: Create tickets
   - **PagerDuty**: Trigger incidents
   - **IP Blocking**: Block malicious IPs
   - **Key Rotation**: Rotate compromised keys
   - **Quarantine**: Isolate compromised resources

**Triggers**:
- Threat alerts (by severity, MITRE technique)
- Incidents (by severity, type)
- Access requests (by risk score)
- Anomalies (by deviation score)
- Manual execution

**Key Features**:
- YAML-based playbook definitions
- Conditional triggers
- Multi-action execution
- Approval workflow
- Audit trail

---

## Data Flow

### 1. Log Ingestion
- Logs arrive at OTel Collector Gateway via OTLP
- Logs are received from various sources (identity providers, network devices, endpoints, applications)

### 2. Log Transformation
- Log Transformation Service normalizes logs
- Converts different formats to standard structure
- Enriches with metadata (source type, timestamps, etc.)

### 3. Event Publishing
- Normalized logs published to NATS event bus
- Subject format: `logs.normalized.{source_type}.{org_id}`
- Message format: JSON with `timestamp`, `source`, `log_data`, `metadata`, `org_id`

### 4. Agent Processing
- **TVA**: Subscribes to all normalized logs, analyzes for threats
- **IGA**: Processes identity/access logs for access requests
- **PBA**: Updates behavior baselines from user/service activity
- **CRA**: Correlates alerts and creates incidents
- **SAA**: Monitors for trigger conditions and executes playbooks

### 5. Storage
- **PostgreSQL**: Stores alerts, incidents, access requests, playbooks, baselines
- **Neo4j**: Stores access graph (users, roles, resources, permissions)
- **pgvector**: Stores embeddings for similarity search

---

## Integration Points

### NATS Event Bus
- **Subjects**: `logs.normalized.{source_type}.{org_id}`
- **Message Format**: JSON
- **Publishers**: Log Transformation Service
- **Subscribers**: TVA, IGA, PBA

### Neo4j Access Graph
- **Nodes**: User, Role, Resource, Permission, Group
- **Relationships**: HAS_ROLE, HAS_PERMISSION, ACCESSES, MEMBER_OF
- **Used By**: IGA (access path analysis, risk scoring)

### PostgreSQL
- **Tables**: 
  - `threat_alerts` (TVA)
  - `access_requests` (IGA)
  - `incidents` (CRA)
  - `persona_baselines` (PBA)
  - `soar_playbooks` (SAA)
  - `playbook_executions` (SAA)
  - `embeddings` (vector storage)

### pgvector
- **Purpose**: Vector similarity search for embeddings
- **Used By**: TVA (anomaly detection), PBA (behavior matching)

---

## Common Use Cases

### Use Case 1: Detecting a Brute Force Attack
1. **TVA** detects multiple failed login attempts
2. Creates threat alert with MITRE technique T1110 (Brute Force)
3. **CRA** correlates multiple alerts from same IP
4. Creates incident with severity HIGH
5. **SAA** triggers playbook to block IP address
6. Sends notification to security team

### Use Case 2: Access Request Approval
1. User requests access to production database (JITA)
2. **IGA** evaluates request:
   - Queries Neo4j for user roles
   - Calculates risk score (0.6 - medium risk)
   - Detects no role drift
   - Recommends approval with 2-hour limit
3. Request approved automatically (low risk)
4. Access granted, expires after 2 hours

### Use Case 3: Anomalous User Behavior
1. User logs in from new IP address at unusual time
2. **PBA** compares to baseline:
   - Baseline shows normal login from office IP during business hours
   - Current login from foreign IP at 2 AM
   - Deviation score: 0.85 (high anomaly)
3. Creates persona anomaly
4. **TVA** receives anomaly, creates threat alert
5. **SAA** triggers playbook to require MFA

### Use Case 4: Multi-Step Attack Investigation
1. **TVA** detects initial access (T1078 - Valid Accounts)
2. **TVA** detects execution (T1059 - Command and Scripting Interpreter)
3. **TVA** detects credential access (T1003 - OS Credential Dumping)
4. **CRA** correlates all alerts:
   - Builds timeline showing attack progression
   - Identifies root cause: compromised user account
   - Estimates blast radius: 5 servers, 3 databases
5. Creates incident with severity CRITICAL
6. **SAA** triggers playbook:
   - Revokes compromised account
   - Rotates all affected keys
   - Creates JIRA ticket
   - Notifies security team

---

## Best Practices

1. **Start with Threat Detection**: Configure TVA first to detect threats
2. **Set Up Access Governance**: Use IGA for all access requests
3. **Create SOAR Playbooks**: Automate common response scenarios
4. **Review Baselines Regularly**: Ensure PBA baselines are accurate
5. **Investigate Incidents**: Use CRA for thorough incident investigation
6. **Monitor MITRE Coverage**: Track which MITRE techniques are detected
7. **Tune Thresholds**: Adjust anomaly and risk thresholds based on your environment

---

## Configuration

### TVA Configuration
- Anomaly threshold: 0.7 (default)
- MITRE mapping: Enabled
- Threat intelligence: Configure feeds

### IGA Configuration
- Risk threshold: 0.7 (default)
- Role drift threshold: 0.2 (default)
- Auto-approval: Based on risk score

### PBA Configuration
- Anomaly threshold: 0.7 (default)
- Minimum samples: 10 (for baseline creation)
- Update frequency: Continuous

### SAA Configuration
- Playbook triggers: Configure per playbook
- Approval required: Per playbook setting
- Action timeouts: 30 seconds (default)

---

## AI Helper

The AI Helper provides context-aware assistance for using the security platform. It:
- Answers questions about how modules work
- Provides step-by-step instructions
- Explains concepts and terminology
- Suggests next steps
- Adapts to the current page/module

**Usage**: Click the chat icon in the bottom-right corner of any security page.


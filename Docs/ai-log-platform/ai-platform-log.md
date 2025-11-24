# AI-Augmented IT Log Management Platform
## Architecture & Agent Flows (Access Management & Threat Vectors)

This document describes an end-to-end architecture for an AI-augmented IT log management platform focused on:

- Identity & access management (IAM, JITA/JITP, PAM)
- Threat vector detection (MITRE ATT&CK, behavioral analytics)
- Correlation & RCA
- SOAR-style automated response

It is structured as:

1. High-level architecture (Mermaid flowchart)
2. Component breakdown
3. Per-agent views with detailed sequence diagrams
4. Integration notes (Vector.dev, OTEL, NATS/Kafka, storage, control plane)

---

## 1. High-Level Architecture (Mermaid)

```mermaid
flowchart LR

  subgraph "Log & Identity Sources"
    S1["Identity Providers\n(Okta / Keycloak / Azure AD / GCP IAM)"]
    S2["JITA / Jump Hosts / PAM Systems"]
    S3["Endpoints\n(Servers / Workstations / Containers)"]
    S4["Network Devices\n(Firewalls / Proxies / WAF / VPN)"]
    S5["Applications\n(API Gateways / Microservices / SaaS)"]
    S6["Threat Intelligence Feeds\n(MITRE / CISA KEV / CVE / IP Reps)"]
  end

  subgraph "Ingestion & Normalization Layer"
    I1["Log Shippers / Agents\n(Vector Agents / Fluent Bit / Beats)"]
    I2["OTEL Collectors\n(OTLP Receivers / Processors)"]
    I3["NATS / Kafka Bus\n(Event Streaming Fabric)"]
  end

  subgraph "Storage & Index Layer"
    ST1["Log Store\n(Loki / VictoriaLogs / S3)"]
    ST2["Security Search / SIEM\n(OpenSearch / Elastic)"]
    ST3["Access Graph DB\n(Neo4j / Arango)"]
    ST4["Feature Store & Embeddings\n(PGVector / Weaviate)"]
  end

  subgraph "AI Agent Layer"
    A1[["Identity Governance Agent\n(Role Drift / Entitlement Risk)"]]
    A2[["Threat Vector Agent\n(MITRE TTP / Behavior Anomaly)"]]
    A3[["Correlation & RCA Agent\n(Cross-Log Storyline)"]]
    A4[["Persona Baseline Agent\n(User / Service Behavior)"]]
    A5[["SOAR Automation Agent\n(Response Playbooks)"]]
  end

  subgraph "Control Plane & UX"
    C1["Access Control Plane\n(JITA / JITP / Policy Engine)"]
    C2["SecOps / AIOps Console\n(Dashboards / Session Graphs)"]
    C3["Policy Authoring UI\n(RBAC / IAM Templates)"]
    C4["SOAR Orchestrator\n(PagerDuty / JIRA / Slack)"]
    C5["Audit & Compliance Portal\n(Reports / Evidence / Trails)"]
  end

  subgraph "External Integrations"
    X1["Ticketing & ITSM\n(JIRA / ServiceNow)"]
    X2["Communication\n(Slack / Teams / Email)"]
    X3["IR Tools\n(EDR / NDR / Forensics)"]
  end

  %% Source to Ingestion
  S1 --"Auth / Access Logs"--> I1
  S2 --"Session / Command Logs"--> I1
  S3 --"Syslog / Endpoint Logs"--> I1
  S4 --"Flow / Firewall Logs"--> I1
  S5 --"App / API Logs"--> I1
  S6 --"Threat Intel Indicators"--> A2

  %% Ingestion Path
  I1 --"Normalize / Tag / Enrich"--> I2
  I2 --"OTLP Export"--> I3
  I3 --"Fan-out Events"--> ST1
  I3 --"Fan-out Events"--> ST2
  I3 --"Access Relationships"--> ST3
  I3 --"Features / Embeddings"--> ST4

  %% Storage to AI Agents
  ST1 --"Raw / Parsed Logs"--> A3
  ST2 --"Security Events / Alerts"--> A2
  ST3 --"Identity & Resource Graph"--> A1
  ST3 --"Path Analysis"--> A3
  ST4 --"Behavior Vectors"--> A4

  %% AI Agents to Control Plane
  A1 --"Access Risk Score / Role Drift Findings"--> C1
  A1 --"Least-Privilege Suggestions"--> C3
  A2 --"Threat Detections / TTP Matches"--> C2
  A3 --"Correlated Incident Timeline / RCA"--> C2
  A4 --"Persona Deviations / Anomalies"--> C2
  A5 --"Playbook Execution Status"--> C4

  %% Control Plane Internal Flows
  C1 --"Approved Access / Deny Decisions"--> S1
  C1 --"JITA Sessions / Tokens"--> S2
  C2 --"Analyst Actions / Triage"--> C4
  C3 --"Policy Updates"--> ST3
  C3 --"Policy-as-Code"--> ST4
  C4 --"Incidents / Tasks"--> X1
  C4 --"Notifications"--> X2
  C5 --"Audit Reports / Evidence"--> X1

  %% SOAR Agent to External Systems
  A5 --"Quarantine / Contain / Block Requests"--> X3
  A5 --"Ticket Create / Update"--> X1
  A5 --"Notify Channels"--> X2
```

---

## 2. Component Breakdown

### 2.1 Log & Identity Sources

- **Identity Providers**: Okta, Keycloak, Azure AD, GCP IAM.
- **JITA / PAM Systems**: Jump hosts, bastion, privileged access management tools.
- **Endpoints**: Linux/Windows servers, workstations, containers, Kubernetes nodes.
- **Network Devices**: Firewalls, WAF, VPN, load balancers, proxies.
- **Applications**: API gateways, internal microservices, SaaS audit logs.
- **Threat Intelligence**: MITRE ATT&CK mappings, CISA KEV, curated CVEs, IP/domain reputation.

### 2.2 Ingestion & Normalization Layer

- **Log Shippers/Agents**: Vector agents, Fluent Bit, Beats; responsible for collecting logs and forwarding to OTEL or central pipeline.
- **OTEL Collectors**: OTLP receivers and processors, performing transformations, sampling, redaction, and routing.
- **NATS / Kafka Event Bus**: Central fan-out fabric for normalized events, decoupling producers and consumers.

### 2.3 Storage & Index Layer

- **Log Store**: Loki/VictoriaLogs/S3 for time-series and raw/parsed log retention.
- **Security Search / SIEM**: OpenSearch/Elastic for structured search and rule-based detections.
- **Access Graph DB**: Neo4j/Arango to represent identities, roles, resources, and permissions as graphs.
- **Feature Store & Embeddings**: PGVector/Weaviate storing user/service behavior embeddings, TTP embeddings, and derived features.

### 2.4 AI Agent Layer

- **Identity Governance Agent (IGA)**: Role drift detection, entitlement risk scoring, least-privilege suggestions.
- **Threat Vector Agent (TVA)**: MITRE TTP mapping, anomaly detection, suspicious pattern detection.
- **Correlation & RCA Agent (CRA)**: Cross-log correlation, attack-path reconstruction, incident storyline/RCA.
- **Persona Baseline Agent (PBA)**: Behavioral baselines for users and services, deviation detection.
- **SOAR Automation Agent (SAA)**: Executes response playbooks (quarantine, key rotation, ticketing, notifications).

### 2.5 Control Plane & UX

- **Access Control Plane**: JITA/JITP engine, policy enforcement, token/session issuance, approvals.
- **SecOps / AIOps Console**: Dashboards, session graphs, risk views, investigation UI.
- **Policy Authoring UI**: RBAC/IAM policy editor, policy-as-code workflows.
- **SOAR Orchestrator**: Integrates with PagerDuty, JIRA, Slack, Teams; executes automation flows.
- **Audit & Compliance Portal**: Displays audit trails, evidence, compliance reports.

### 2.6 External Integrations

- **Ticketing & ITSM**: JIRA, ServiceNow, etc.
- **Communication Channels**: Slack, Teams, email.
- **IR Tools**: EDR/NDR/forensics platforms for deeper investigation and containment.

---

## 3. Per-Agent Views & Sequence Diagrams

The following sections slice the architecture by agent and provide detailed sequence diagrams for the main flows.

---

### 3.1 Identity Governance Agent (IGA) Flow

**Use case:** User requests privileged access; agent scores risk based on identity & behavior; control plane decides approve/deny and logs actions.

```mermaid
sequenceDiagram
    participant User as User
    participant UI as Access Portal (UI)
    participant ACP as Access Control Plane (JITA/JITP)
    participant IGA as Identity Governance Agent
    participant AGDB as Access Graph DB (Neo4j)
    participant FS as Feature Store / Embeddings
    participant SIEM as SIEM / Search
    participant AUD as Audit & Compliance Store

    User->>UI: Submit access request (resource, duration, justification)
    UI->>ACP: API: CreateAccessRequest(payload)
    ACP->>SIEM: Query recent security events for user/resource
    ACP->>AGDB: Fetch identity graph (groups, roles, relationships)
    ACP->>FS: Fetch behavioral profile (embeddings, baseline stats)

    ACP->>IGA: EvaluateAccessRisk(request, graph, features, events)
    IGA->>IGA: Compute risk score (role drift, abnormal access, blast radius)
    IGA-->>ACP: RiskScore + Insights + RecommendedScope

    ACP->>UI: Display risk score & recommendation (e.g., limited duration)
    alt Auto-approval policy satisfied
        ACP->>ACP: Apply policy (auto-approve with constraints)
        ACP-->>UI: Access approved (token/session details)
    else Manual approval required
        ACP->>Approver: Send approval task/notification
        Approver-->>ACP: Approve/Deny decision
        ACP-->>UI: Decision + rationale
    end

    ACP->>AUD: Log decision, risk score, justification, approver
    ACP->>SIEM: Emit audit event for correlation
```

**Key IGA responsibilities:**

- Combine **graph context** (who can access what) with **behavioral context** (what they usually do).
- Detect **role drift**, over-privileged users, and suspicious resource targeting.
- Return **risk score, explanation, and recommended scope (role/time restriction)**.

---

### 3.2 Threat Vector Agent (TVA) Flow

**Use case:** Logs indicate suspicious behavior; TVA maps to MITRE TTPs and raises a threat alert with enriched context.

```mermaid
sequenceDiagram
    participant Src as Log Sources (Apps/Endpoints/Network)
    participant Vec as Vector / OTEL Collectors
    participant Bus as NATS/Kafka Bus
    participant ST as Log Store / SIEM
    participant TVA as Threat Vector Agent
    participant TI as Threat Intel Feeds (MITRE/CISA/CVEs)
    participant Cns as SecOps Console
    participant SOAR as SOAR Orchestrator

    Src->>Vec: Emit raw logs (auth, process, network, API)
    Vec->>Vec: Parse, normalize, enrich (tenant, region, etc.)
    Vec->>Bus: Publish normalized events
    Bus->>ST: Persist logs/events

    Bus->>TVA: Stream of enriched events
    TVA->>TI: Fetch TTP patterns / indicators
    TVA->>TVA: Convert events to embeddings & match against TTPs
    TVA-->>TVA: Identify suspicious sequences (e.g., lateral movement)

    TVA-->>ST: Write enriched detection event (threat alert)
    TVA-->>Cns: Push high-priority alert + TTP mapping + explanation

    alt Auto-response policy enabled
        Cns->>SOAR: Trigger response playbook (containment)
        SOAR->>SOAR: Execute actions (block IP, disable account, isolate host)
        SOAR-->>Cns: Update alert state, attach execution logs
    else Manual investigation
        Cns->>Analyst: Show alert details & recommended actions
    end
```

**Key TVA responsibilities:**

- Map event patterns to **MITRE ATT&CK techniques**, using embeddings and rules.
- Identify **multi-step attack patterns** (e.g., persistence → lateral movement → exfil).
- Provide **explainable threat alerts** with TTP labels and recommended remediation.

---

### 3.3 Correlation & RCA Agent (CRA) Flow

**Use case:** Multiple alerts and logs exist; CRA builds a timeline and narrative of the incident, linking identity, network, and application layers.

```mermaid
sequenceDiagram
    participant Alerts as Alerts (TVA / Rules)
    participant ST as SIEM / Log Store
    participant CRA as Correlation & RCA Agent
    participant AGDB as Access Graph DB
    participant FS as Feature Store
    participant Cns as SecOps Console
    participant AUD as Audit & Compliance Store

    Alerts->>ST: Store detection events and metadata
    Cns->>CRA: Request RCA for incident (incidentId)

    CRA->>ST: Pull logs & alerts around incident time window
    CRA->>AGDB: Fetch relationships (user -> host -> service -> data)
    CRA->>FS: Fetch behavior baselines & anomaly scores

    CRA->>CRA: Build attack graph & timeline
    CRA->>CRA: Identify root cause and blast radius
    CRA-->>Cns: RCA summary (timeline, impact, root cause, evidence)

    Cns->>AUD: Store RCA report and evidence bundle
```

**Key CRA responsibilities:**

- Correlate **signals from multiple agents + raw logs**.
- Build human-readable **storyline and timeline**.
- Estimate **blast radius** and impacted entities.

---

### 3.4 Persona Baseline Agent (PBA) Flow

**Use case:** Continuous learning of normal behavior for users/services; raise deviations for identity or service misuse.

```mermaid
sequenceDiagram
    participant Src as Log Sources
    participant Vec as Vector / OTEL
    participant Bus as NATS/Kafka
    participant ST as Feature Store / Embeddings
    participant PBA as Persona Baseline Agent
    participant Cns as SecOps Console

    Src->>Vec: Emit events (logins, API calls, DB queries)
    Vec->>Bus: Normalized events with identity/service tags
    Bus->>PBA: Stream of behavior events

    PBA->>PBA: Train/update embeddings per user/service
    PBA->>ST: Store/update persona embeddings & baselines

    PBA->>PBA: Compute deviation score for new events
    alt Deviation exceeds threshold
        PBA-->>Cns: Anomaly alert (persona deviation)
    else
        PBA-->>ST: Update baseline stats only
    end
```

**Key PBA responsibilities:**

- Maintain **per-identity and per-service embeddings**.
- Detect **anomalous usage** independent of static policy.
- Feed anomaly scores into IGA, TVA, and CRA.

---

### 3.5 SOAR Automation Agent (SAA) Flow

**Use case:** On high-confidence threats or policy violation, SAA executes playbooks: isolation, revocation, ticketing, notification.

```mermaid
sequenceDiagram
    participant Agent as AI Agents (IGA/TVA/CRA/PBA)
    participant SOAR as SOAR Automation Agent
    participant Orchestrator as SOAR Orchestrator
    participant ITSM as Ticketing (JIRA/ServiceNow)
    participant Comm as ChatOps (Slack/Teams/Email)
    participant IR as IR Tools (EDR/NDR/Firewall)
    participant AUD as Audit & Compliance Store

    Agent-->>SOAR: RequestPlaybookExecution(incidentId, playbook, context)
    SOAR->>Orchestrator: Start playbook run

    Orchestrator->>IR: API calls (isolate host, block IP, disable user)
    Orchestrator->>ITSM: Create/Update incident ticket
    Orchestrator->>Comm: Send notifications to channels

    Orchestrator-->>SOAR: Execution status, logs
    SOAR-->>AUD: Store playbook run details, timestamps, outcomes
```

**Key SAA responsibilities:**

- Provide **policy-aware automation**, gated by risk & confidence.
- Integrate with **IR tools, ticketing, ChatOps**.
- Maintain **audit trails** for all automated actions.

---

## 4. Integration Notes (Vector.dev, OTEL, Backend)

At a platform level:

- **Vector.dev agents**: Ship logs from identity providers, PAM/jump hosts, endpoints, and network gear.
- **OTEL collectors**: Serve as a central pipeline: OTLP ingest, enrichment, redaction, multi-tenant routing.
- **Event bus (NATS/Kafka)**: Decouple log ingestion from AI agents and storage.
- **Python backend**: Expose API endpoints for UI, house AI agent orchestrators and models, and integrate with Vector/OTEL via HTTP/gRPC/OTLP.
- **React UI**: Implements dashboards, RCA views, policy editors, and JITA/JITP workflows on top of backend APIs.
- **Storage**: Use a mix of time-series/log databases, graph DB, and vector stores for the agents’ needs.

This .md file can be used as the core design spec in a repo (e.g., `/docs/ai-log-platform-architecture.md`).

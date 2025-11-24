flowchart LR
    %% Core Sections
    subgraph Ingestion["Log & Event Ingestion Layer"]
        A1[<b>Identity Logs</b><br/>Okta, Keycloak, Azure AD, GCP IAM]
        A2[<b>Access Logs</b><br/>JITA/JITP, sudo, session events]
        A3[<b>System Logs</b><br/>Linux, Windows, daemon, auth.log]
        A4[<b>Network Logs</b><br/>VPC Flow, firewall, proxy]
        A5[<b>Application Logs</b><br/>API Gateway, microservices]
        A6[<b>Threat Intelligence</b><br/>MITRE, CISA KEV, CVE DB]
    end

    subgraph Pipeline["Log Pipeline Layer"]
        P1[Vector.dev<br/>Parsing / Normalization]
        P2[OTEL Collector<br/>OTLP → Transform → Export]
        P3[NATS Event Bus<br/>Async fanout / queue]
        P4[Feature Store ETL<br/>Anomaly Features / Embeddings]
    end

    subgraph Storage["Storage & Index Layer"]
        S1[Observability DB<br/>Loki/VictoriaLogs]
        S2[Graph Store<br/>Neo4j/ArangoDB - Access Graph]
        S3[Embedding Index<br/>PGVector/Weaviate]
        S4[SIEM Store<br/>Elasticsearch/OpenSearch]
    end

    subgraph AI["AI Agent Layer"]
        AG1[[Identity Governance Agent<br/>Role Drift • JIT Access Risk Score]]
        AG2[[Threat Vector Agent<br/>MITRE TTP Matching • Anomaly Detection]]
        AG3[[Correlation Agent<br/>Cross-log correlation • RCA generation]]
        AG4[[Persona Baseline Agent<br/>User/Service Behavior Modeling]]
        AG5[[SOAR Automation Agent<br/>Quarantine • Key Rotation • Ticketing]]
    end

    subgraph Control["Control Plane & UI"]
        C1[Access Control Plane<br/>JITA/JITP Engine]
        C2[AIOps/SecOps Dashboard<br/>Risk Heatmaps, Session Graphs]
        C3[Policy Engine<br/>RBAC/IAM Rule Generator]
        C4[SOAR Orchestrator<br/>PagerDuty/JIRA/Slack Integration]
        C5[Audit & Compliance UI<br/>Evidence, Reports, Trails]
    end

    %% Flows
    A1 --> P1
    A2 --> P1
    A3 --> P1
    A4 --> P1
    A5 --> P1
    A6 --> AG2
    
    P1 --> P2
    P2 --> P3
    P3 --> P4

    P4 --> S1
    P4 --> S2
    P4 --> S3
    P4 --> S4

    S1 --> AG3
    S2 --> AG1
    S3 --> AG4
    S4 --> AG2

    AG1 --> C1
    AG2 --> C2
    AG3 --> C2
    AG4 --> C2
    AG5 --> C4

    C1 --> C3
    C2 --> C3
    C3 --> AG5
    C4 --> C5
    C5 --> C2

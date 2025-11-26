1. Operating System Logs
1.1 Linux / Unix

/var/log/auth.log (auth events)

/var/log/secure (SSH, sudo)

/var/log/messages

/var/log/syslog

/var/log/kern.log

Cron logs

Systemd journal logs (via journald)

1.2 Windows

Security event logs

Application logs

System logs

PowerShell logs

Sysmon logs (process trees, network events, registry changes)

2. Identity & Access Logs
2.1 Identity Providers

Okta system logs

Azure AD sign-in logs

PingFed, PingOne

Google Workspace login audit

Keycloak audit events

AWS IAM CloudTrail entries

GCP IAM audit logs

2.2 Authentication & SSO

SAML/OIDC events

MFA push attempts

Session tokens

OAuth app access

Privilege elevation

Password resets

Conditional access decisions

3. Privileged Access & PAM Logs

CyberArk privileged session logs

BeyondTrust logs

HashiCorp Vault audit logs

JITA/JIT elevation events

Bastion / Jumpbox SSH session logs

Sudo transcripts

4. Endpoint Security Logs
4.1 EDR/XDR

CrowdStrike Falcon telemetry

SentinelOne logs

CarbonBlack logs

Defender for Endpoint

Tanium agent logs

Includes:

Process creation

Executable hashes

Lateral movement alerts

File modifications

Behavioral detections

4.2 MDM / Device Management

Intune

Jamf

Workspace ONE

ChromeOS management

5. Network & Perimeter Logs
5.1 Firewalls / NGFW

Palo Alto firewall logs

Fortinet FortiGate logs

CheckPoint logs

Cisco ASA / FTD logs

SonicWall

Types:

Allow/deny events

NAT logs

Connection logs

IPS alerts

VPN logs

5.2 WAF / IDS / IPS

Cloudflare WAF

AWS WAF

Snort

Suricata

Imperva

Akamai Kona

5.3 Network Equipment Logs

Routers, switches, load balancers

DHCP logs

DNS logs

6. Cloud Platform Logs
6.1 AWS

CloudTrail

CloudWatch logs

VPC Flow Logs

ALB/NLB/ELB logs

GuardDuty

Security Hub findings

6.2 Azure

Azure Activity Logs

Azure AD logs

NSG flow logs

Sentinel detection logs

6.3 GCP

Audit logs

VPC Flow logs

Cloud Armor logs

Event Threat Detection logs

7. Application Logs

Web server logs (Nginx, Apache)

API gateway logs (Kong, Apigee, Istio, Envoy)

Framework logs (Django, Flask, Spring Boot)

Application error logs

Backend microservice logs

Frontend beacon logs

Serverless logs (AWS Lambda, GCP Cloud Functions)

8. Database Logs

MySQL/Postgres slow query logs

DB audit logs

SQL Server Extended Events

MongoDB audit logs

Redis logs

Elasticsearch cluster logs

9. Security Product Logs

SIEM alerts from other platforms

Threat intelligence feeds

CVE/patching systems

DLP systems

CASB (Cloud Access Security Broker)

SASE platforms

10. Observability Logs
10.1 Metrics & Traces via OTEL

Splunk Observability Cloud supports:

OTLP logs

OTLP metrics

OTLP traces

Service maps

Distributed tracing

10.2 APM / Infrastructure

K8s cluster logs (kube-apiserver, scheduler, controller-manager)

Container logs

Node logs

Host-level metrics

11. DevOps & CI/CD Logs

GitHub/GitLab audit logs

Jenkins build logs

ArgoCD/Argo Rollouts logs

Terraform Cloud audit

CICD pipeline logs

Package manager logs

12. Business & Custom Logs

Transaction logs

Payment logs

User behavior logs

Custom JSON logs

IoT logs

Manufacturing logs

Healthcare/financial system logs

Splunk supports any custom schema, JSON, protobuf, CSV, XML, syslog, or even raw text.

13. How Splunk Ingests Logs

Splunk supports ingestion through:

13.1 Universal Forwarder

Installed on machines

Tails files

Streams to Splunk indexers

Lightweight and secure

13.2 Heavy Forwarder

Parsing

Filtering

Routing

Enrichment

13.3 Splunk Cloud HTTP Event Collector (HEC)

Best for apps, microservices, OTEL, Vector.dev

Supports JSON logs

13.4 Syslog

Network appliances

Firewalls

Switches

13.5 APIs / Modular Inputs

Salesforce

Jira

SNMP traps

Cloud provider APIs

13.6 OTLP / Observability Collector
13.7 Vector.dev / OTEL collectors

Export logs to Splunk HEC

Normalize + enrich before shipping
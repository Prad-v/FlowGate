"""add_comprehensive_log_formats

Revision ID: 5c26f7393ff2
Revises: f4044c36b9dd
Create Date: 2025-11-24 06:25:56.331224

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import json

# revision identifiers, used by Alembic.
revision = '5c26f7393ff2'
down_revision = 'f4044c36b9dd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add comprehensive log formats from log-formats.md"""
    connection = op.get_bind()
    
    # Comprehensive log format templates organized by category
    templates = [
        # Operating System Logs - Linux/Unix
        {
            'format_name': 'linux_auth_log',
            'display_name': 'Linux Auth Log (/var/log/auth.log)',
            'format_type': 'source',
            'description': 'Linux authentication events from /var/log/auth.log',
            'sample_logs': 'Jan  2 10:30:45 hostname sshd[1234]: Accepted publickey for user from 192.168.1.100 port 12345 ssh2',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<service>\S+)\[(?P<pid>\d+)\]:\s+(?P<message>.*)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "service", "pid", "message", "user", "source_ip"]},
        },
        {
            'format_name': 'linux_secure',
            'display_name': 'Linux Secure Log (/var/log/secure)',
            'format_type': 'source',
            'description': 'Linux SSH and sudo logs from /var/log/secure',
            'sample_logs': 'Jan  2 10:30:45 hostname sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<service>\S+):\s+(?P<message>.*)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "service", "message", "user", "command"]},
        },
        {
            'format_name': 'linux_messages',
            'display_name': 'Linux Messages Log (/var/log/messages)',
            'format_type': 'source',
            'description': 'Linux system messages log',
            'sample_logs': 'Jan  2 10:30:45 hostname kernel: [12345.678] IPv4: martian source 192.168.1.1 from 10.0.0.1',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+(?P<component>\S+):\s+(?P<message>.*)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "component", "message"]},
        },
        {
            'format_name': 'linux_kern_log',
            'display_name': 'Linux Kernel Log (/var/log/kern.log)',
            'format_type': 'source',
            'description': 'Linux kernel log messages',
            'sample_logs': 'Jan  2 10:30:45 hostname kernel: [12345.678] audit: type=1400 audit(1704192645.123:456): apparmor="ALLOWED" operation="open" profile="/usr/sbin/sshd" name="/etc/passwd"',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+kernel:\s+\[(?P<timestamp>[^\]]+)\]\s+(?P<message>.*)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "timestamp", "message", "audit_type", "operation"]},
        },
        {
            'format_name': 'cron_logs',
            'display_name': 'Cron Logs',
            'format_type': 'source',
            'description': 'Linux cron job execution logs',
            'sample_logs': 'Jan  2 10:30:01 hostname CRON[1234]: (root) CMD (/usr/bin/backup.sh)',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+CRON\[(?P<pid>\d+)\]:\s+\((?P<user>\S+)\)\s+CMD\s+\((?P<command>[^)]+)\)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "pid", "user", "command"]},
        },
        {
            'format_name': 'systemd_journal',
            'display_name': 'Systemd Journal Logs',
            'format_type': 'source',
            'description': 'Systemd journald structured logs (JSON format)',
            'sample_logs': '{"__CURSOR":"s=abc123","__REALTIME_TIMESTAMP":"1704192645123456","__MONOTONIC_TIMESTAMP":"1234567890","_BOOT_ID":"abc-def-123","PRIORITY":"6","_UID":"0","_GID":"0","_CAP_EFFECTIVE":"3fffffffff","_SYSTEMD_CGROUP":"/system.slice/sshd.service","_SYSTEMD_UNIT":"sshd.service","_SYSTEMD_SLICE":"system.slice","_MACHINE_ID":"abc123","_HOSTNAME":"hostname","MESSAGE":"User logged in","_PID":"1234","_COMM":"sshd","_EXE":"/usr/sbin/sshd","_CMDLINE":"sshd: user@pts/0","_AUDIT_SESSION":"1","_AUDIT_LOGINUID":"1000","_SYSTEMD_OWNER_UID":"0","_SYSTEMD_SESSION":"1","_SYSTEMD_USER_UNIT":"-","_SYSTEMD_USER_SLICE":"-","_SELINUX_CONTEXT":"-","_SOURCE_REALTIME_TIMESTAMP":"1704192645123456"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["__CURSOR", "__REALTIME_TIMESTAMP", "PRIORITY", "_SYSTEMD_UNIT", "MESSAGE", "_PID", "_COMM", "_HOSTNAME"]},
        },
        # Operating System Logs - Windows
        {
            'format_name': 'windows_security_events',
            'display_name': 'Windows Security Event Logs',
            'format_type': 'source',
            'description': 'Windows Security event logs (Event ID 4624, 4625, etc.)',
            'sample_logs': '2024-01-02 10:30:45,123 Security 4624 An account was successfully logged on. Subject: Security ID: S-1-5-18 Account Name: SYSTEM Account Domain: NT AUTHORITY Logon ID: 0x3e7 Logon Type: 3 New Logon: Security ID: S-1-5-21-1234567890-123456789-123456789-1234 Account Name: john.doe Account Domain: EXAMPLE Process Information: Process ID: 0x1234 Process Name: C:\\Windows\\System32\\lsass.exe Network Information: Workstation Name: WORKSTATION-01 Source Network Address: 192.168.1.100 Source Port: 12345',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<log_type>\w+)\s+(?P<event_id>\d+)\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "log_type", "event_id", "message", "account_name", "domain", "source_ip", "logon_type"]},
        },
        {
            'format_name': 'windows_application_logs',
            'display_name': 'Windows Application Logs',
            'format_type': 'source',
            'description': 'Windows Application event logs',
            'sample_logs': '2024-01-02 10:30:45,123 Application 1000 Error: Application failed to start. Exception: System.NullReferenceException at MyApp.Main()',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<log_type>\w+)\s+(?P<event_id>\d+)\s+(?P<level>\w+):\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "log_type", "event_id", "level", "message", "application"]},
        },
        {
            'format_name': 'windows_system_logs',
            'display_name': 'Windows System Logs',
            'format_type': 'source',
            'description': 'Windows System event logs',
            'sample_logs': '2024-01-02 10:30:45,123 System 6008 The previous system shutdown was unexpected.',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<log_type>\w+)\s+(?P<event_id>\d+)\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "log_type", "event_id", "message", "source"]},
        },
        {
            'format_name': 'powershell_logs',
            'display_name': 'PowerShell Logs',
            'format_type': 'source',
            'description': 'Windows PowerShell execution and script block logs',
            'sample_logs': '2024-01-02 10:30:45,123 PowerShell 4104 ScriptBlock Text: Get-Process | Where-Object {$_.CPU -gt 100}',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+PowerShell\s+(?P<event_id>\d+)\s+(?P<event_type>\w+)\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "event_id", "event_type", "message", "script_block", "user", "hostname"]},
        },
        {
            'format_name': 'sysmon_logs',
            'display_name': 'Sysmon Logs',
            'format_type': 'source',
            'description': 'Windows Sysmon (System Monitor) logs for process trees, network events, and registry changes',
            'sample_logs': '2024-01-02 10:30:45,123 Microsoft-Windows-Sysmon/Operational 1 Process Create: UtcTime: 2024-01-02 10:30:45.123 ProcessGuid: {12345678-1234-1234-1234-123456789abc} ProcessId: 1234 Image: C:\\Windows\\System32\\cmd.exe CommandLine: "cmd.exe /c dir" User: EXAMPLE\\john.doe LogonGuid: {87654321-4321-4321-4321-cba987654321}',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<source>\S+)\s+(?P<event_id>\d+)\s+(?P<event_type>[^:]+):\s+(?P<details>.*)$"},
            'schema': {"fields": ["timestamp", "source", "event_id", "event_type", "details", "process_guid", "process_id", "image", "command_line", "user"]},
        },
        # Identity & Access Logs - Additional Providers
        {
            'format_name': 'pingfed_logs',
            'display_name': 'PingFederate / PingOne Logs',
            'format_type': 'source',
            'description': 'PingFederate and PingOne identity provider logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [PingFederate] SSO_LOGIN_SUCCESS user="john.doe@example.com" session_id="sess_abc123" idp="https://idp.example.com" sp="https://sp.example.com" assertion_id="assert_123456"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\"\s+session_id=\"(?P<session_id>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "session_id", "idp", "sp"]},
        },
        {
            'format_name': 'google_workspace_audit',
            'display_name': 'Google Workspace Login Audit',
            'format_type': 'source',
            'description': 'Google Workspace login and access audit logs',
            'sample_logs': '{"kind":"admin#reports#activity","id":{"time":"2024-01-02T10:30:45.123Z","uniqueQualifier":"123456","applicationName":"login"},"etag":"abc123","actor":{"callerType":"USER","email":"user@example.com","profileId":"123456789"},"ipAddress":"192.168.1.100","events":[{"type":"login","name":"login_success","parameters":[{"name":"login_type","value":"web"},{"name":"user_agent","value":"Mozilla/5.0"}]}]}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["kind", "id", "actor", "ipAddress", "events", "type", "name"]},
        },
        {
            'format_name': 'keycloak_audit',
            'display_name': 'Keycloak Audit Events',
            'format_type': 'source',
            'description': 'Keycloak identity and access management audit logs',
            'sample_logs': '{"time":1704192645123,"realmId":"master","type":"LOGIN","userId":"abc-123-def","sessionId":"sess-456","ipAddress":"192.168.1.100","userAgent":"Mozilla/5.0","details":{"auth_method":"password","auth_type":"code"},"error":null}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["time", "realmId", "type", "userId", "sessionId", "ipAddress", "userAgent", "details", "error"]},
        },
        # Privileged Access & PAM Logs
        {
            'format_name': 'cyberark_logs',
            'display_name': 'CyberArk Privileged Session Logs',
            'format_type': 'source',
            'description': 'CyberArk privileged access management session logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [CyberArk] SESSION_START user="admin" target="server-01" account="root@server-01" session_id="sess_abc123" ip="192.168.1.100"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\"\s+target=\"(?P<target>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "target", "account", "session_id", "ip"]},
        },
        {
            'format_name': 'beyondtrust_logs',
            'display_name': 'BeyondTrust Logs',
            'format_type': 'source',
            'description': 'BeyondTrust privileged access management logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [BeyondTrust] SESSION_START user="admin" target="server-01" account="root" session_id="sess_abc123"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "target", "account", "session_id"]},
        },
        {
            'format_name': 'vault_audit',
            'display_name': 'HashiCorp Vault Audit Logs',
            'format_type': 'source',
            'description': 'HashiCorp Vault secret management audit logs',
            'sample_logs': '{"time":"2024-01-02T10:30:45.123Z","type":"request","auth":{"client_token":"hvs.abc123","accessor":"accessor_123","display_name":"user","policies":["default","admin"],"token_policies":["default","admin"],"metadata":{"username":"john.doe"}},"request":{"id":"req-123","operation":"read","path":"secret/data/my-secret","remote_address":"192.168.1.100"},"response":{"mount_type":"kv"}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["time", "type", "auth", "request", "response", "error"]},
        },
        {
            'format_name': 'jita_jit_logs',
            'display_name': 'JITA/JIT Elevation Events',
            'format_type': 'source',
            'description': 'Just-In-Time Access (JITA/JIT) privilege elevation event logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [JIT] ELEVATION_REQUEST user="john.doe" role="admin" target="server-01" duration=3600 reason="maintenance" status="approved"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "role", "target", "duration", "reason", "status"]},
        },
        {
            'format_name': 'bastion_ssh_logs',
            'display_name': 'Bastion / Jumpbox SSH Session Logs',
            'format_type': 'source',
            'description': 'SSH session logs from bastion hosts and jumpboxes',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [Bastion] SSH_SESSION_START user="john.doe" source_ip="192.168.1.100" target="server-01" session_id="sess_abc123"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+user=\"(?P<user>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "user", "source_ip", "target", "session_id"]},
        },
        {
            'format_name': 'sudo_transcripts',
            'display_name': 'Sudo Transcripts',
            'format_type': 'source',
            'description': 'Sudo command execution transcripts',
            'sample_logs': 'Jan  2 10:30:45 hostname sudo: user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/ls -la',
            'parser_config': {"type": "regex", "regex": r"^(?P<month>\w+)\s+(?P<day>\d+)\s+(?P<time>\d{2}:\d{2}:\d{2})\s+(?P<hostname>\S+)\s+sudo:\s+(?P<user>\S+)\s+:\s+TTY=(?P<tty>\S+)\s+;\s+PWD=(?P<pwd>[^;]+)\s+;\s+USER=(?P<target_user>\S+)\s+;\s+COMMAND=(?P<command>.*)$"},
            'schema': {"fields": ["month", "day", "time", "hostname", "user", "tty", "pwd", "target_user", "command"]},
        },
        # Endpoint Security Logs - EDR/XDR
        {
            'format_name': 'crowdstrike_falcon',
            'display_name': 'CrowdStrike Falcon Telemetry',
            'format_type': 'source',
            'description': 'CrowdStrike Falcon endpoint detection and response telemetry logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","eventType":"ProcessRollup2","ComputerName":"hostname","UserName":"user","ProcessId":1234,"ParentProcessId":5678,"CommandLine":"cmd.exe /c dir","MD5Hash":"abc123def456","SHA256Hash":"def456abc123","FileName":"cmd.exe","FilePath":"C:\\Windows\\System32\\cmd.exe"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "eventType", "ComputerName", "UserName", "ProcessId", "ParentProcessId", "CommandLine", "MD5Hash", "SHA256Hash", "FileName", "FilePath"]},
        },
        {
            'format_name': 'sentinelone_logs',
            'display_name': 'SentinelOne Logs',
            'format_type': 'source',
            'description': 'SentinelOne endpoint protection logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","eventType":"process","agentId":"abc123","hostname":"hostname","username":"user","processName":"cmd.exe","processPath":"C:\\Windows\\System32\\cmd.exe","commandLine":"cmd.exe /c dir","parentProcessName":"explorer.exe","threatLevel":"malicious","threatName":"Trojan.Generic"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "eventType", "agentId", "hostname", "username", "processName", "processPath", "commandLine", "parentProcessName", "threatLevel", "threatName"]},
        },
        {
            'format_name': 'carbonblack_logs',
            'display_name': 'CarbonBlack Logs',
            'format_type': 'source',
            'description': 'CarbonBlack endpoint detection and response logs',
            'sample_logs': '{"timestamp":1704192645123,"event_type":"filemod","process_guid":"abc-123-def","process_name":"cmd.exe","process_path":"C:\\Windows\\System32\\cmd.exe","cmdline":"cmd.exe /c dir","parent_guid":"def-456-abc","filemod_type":"created","filemod_name":"output.txt","filemod_path":"C:\\temp\\output.txt"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "event_type", "process_guid", "process_name", "process_path", "cmdline", "parent_guid", "filemod_type", "filemod_name", "filemod_path"]},
        },
        {
            'format_name': 'defender_endpoint',
            'display_name': 'Microsoft Defender for Endpoint',
            'format_type': 'source',
            'description': 'Microsoft Defender for Endpoint security logs',
            'sample_logs': '{"Timestamp":"2024-01-02T10:30:45.123Z","EventType":"ProcessCreation","MachineId":"abc123","ComputerName":"hostname","AccountName":"user","AccountDomain":"EXAMPLE","ProcessId":1234,"ProcessCommandLine":"cmd.exe /c dir","ProcessCreationTime":"2024-01-02T10:30:45.123Z","FileName":"cmd.exe","SHA1":"abc123def456","MD5":"def456abc123"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["Timestamp", "EventType", "MachineId", "ComputerName", "AccountName", "AccountDomain", "ProcessId", "ProcessCommandLine", "ProcessCreationTime", "FileName", "SHA1", "MD5"]},
        },
        {
            'format_name': 'tanium_logs',
            'display_name': 'Tanium Agent Logs',
            'format_type': 'source',
            'description': 'Tanium endpoint management and security logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [Tanium] PROCESS_CREATE hostname="hostname" user="user" process="cmd.exe" pid=1234 parent_pid=5678 command_line="cmd.exe /c dir"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+hostname=\"(?P<hostname>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "hostname", "user", "process", "pid", "parent_pid", "command_line"]},
        },
        # Network & Perimeter Logs - Firewalls
        {
            'format_name': 'palo_alto_firewall',
            'display_name': 'Palo Alto Firewall Logs',
            'format_type': 'source',
            'description': 'Palo Alto Networks firewall traffic and threat logs',
            'sample_logs': '2024-01-02 10:30:45,123 receive_time=2024-01-02 10:30:45 serial_number=001234567890 type=traffic subtype=start action=allow src=192.168.1.100 dst=10.0.0.1 sport=12345 dport=80 proto=tcp app=web-browsing rule=allow-web user=john.doe',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+receive_time=(?P<receive_time>[^\s]+)\s+serial_number=(?P<serial_number>[^\s]+)\s+type=(?P<type>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "receive_time", "serial_number", "type", "subtype", "action", "src", "dst", "sport", "dport", "proto", "app", "rule", "user"]},
        },
        {
            'format_name': 'fortinet_fortigate',
            'display_name': 'Fortinet FortiGate Logs',
            'format_type': 'source',
            'description': 'Fortinet FortiGate firewall and security logs',
            'sample_logs': 'date=2024-01-02 time=10:30:45 devname=FG-01 devid=FGVM000000000001 logid=0000000013 type=traffic subtype=forward level=notice vd=root srcip=192.168.1.100 srcport=12345 dstip=10.0.0.1 dstport=80 srcintf="port1" dstintf="port2" action=accept policyid=1 sessionid=1234567890',
            'parser_config': {"type": "regex", "regex": r"^date=(?P<date>[^\s]+)\s+time=(?P<time>[^\s]+)\s+devname=(?P<devname>[^\s]+).*$"},
            'schema': {"fields": ["date", "time", "devname", "devid", "logid", "type", "subtype", "level", "srcip", "srcport", "dstip", "dstport", "action", "policyid", "sessionid"]},
        },
        {
            'format_name': 'checkpoint_logs',
            'display_name': 'CheckPoint Logs',
            'format_type': 'source',
            'description': 'CheckPoint firewall and security logs',
            'sample_logs': '2024-01-02 10:30:45,123 [gateway-01] action:accept src:192.168.1.100 dst:10.0.0.1 proto:tcp sport:12345 dport:80 service:http rule:allow-web user:john.doe',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+\[(?P<gateway>[^\]]+)\]\s+action:(?P<action>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "gateway", "action", "src", "dst", "proto", "sport", "dport", "service", "rule", "user"]},
        },
        {
            'format_name': 'cisco_asa_ftd',
            'display_name': 'Cisco ASA / FTD Logs',
            'format_type': 'source',
            'description': 'Cisco ASA and Firepower Threat Defense logs',
            'sample_logs': '%ASA-6-106100: access-list ACL-IN permitted tcp outside/192.168.1.100(12345) -> inside/10.0.0.1(80) hit-cnt 1 first hit [0xabc123, 0xdef456]',
            'parser_config': {"type": "regex", "regex": r"^%ASA-(?P<severity>\d+)-(?P<message_id>\d+):\s+(?P<message>.*)$"},
            'schema': {"fields": ["severity", "message_id", "message", "src_interface", "src_ip", "src_port", "dst_interface", "dst_ip", "dst_port", "protocol", "action"]},
        },
        {
            'format_name': 'sonicwall_logs',
            'display_name': 'SonicWall Logs',
            'format_type': 'source',
            'description': 'SonicWall firewall and security logs',
            'sample_logs': '2024-01-02 10:30:45,123 id=firewall sn=001234567890 time="2024-01-02 10:30:45" fw=192.168.1.1 pri=6 c=64 m=1 msg="Connection opened" src=192.168.1.100:12345 dst=10.0.0.1:80 proto=tcp action=allow',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+id=(?P<id>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "id", "sn", "time", "fw", "pri", "c", "m", "msg", "src", "dst", "proto", "action"]},
        },
        # Network & Perimeter Logs - WAF/IDS/IPS
        {
            'format_name': 'cloudflare_waf',
            'display_name': 'Cloudflare WAF Logs',
            'format_type': 'source',
            'description': 'Cloudflare Web Application Firewall logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","action":"block","clientIP":"192.168.1.100","clientRequestHost":"example.com","clientRequestMethod":"GET","clientRequestURI":"/api/users","clientRequestHTTPVersion":"HTTP/1.1","edgeResponseStatus":403,"ruleId":"100000","ruleMessage":"SQL injection attempt detected","userAgent":"Mozilla/5.0"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "action", "clientIP", "clientRequestHost", "clientRequestMethod", "clientRequestURI", "edgeResponseStatus", "ruleId", "ruleMessage", "userAgent"]},
        },
        {
            'format_name': 'aws_waf',
            'display_name': 'AWS WAF Logs',
            'format_type': 'source',
            'description': 'AWS Web Application Firewall logs',
            'sample_logs': '{"timestamp":1704192645123,"formatVersion":1,"webaclId":"arn:aws:wafv2:us-east-1:123456789012:regional/webacl/example/abc123","terminatingRuleId":"Default_Action","terminatingRuleType":"REGULAR","action":"ALLOW","httpRequest":{"requestId":"req-123","clientIp":"192.168.1.100","country":"US","headers":[{"name":"Host","value":"example.com"}],"uri":"/api/users","args":"","httpVersion":"HTTP/1.1","httpMethod":"GET","requestHeaders":[],"requestBody":""},"rateBasedRuleList":[],"nonTerminatingMatchingRules":[],"requestHeadersInserted":null,"responseCodeSent":null}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "formatVersion", "webaclId", "terminatingRuleId", "action", "httpRequest", "rateBasedRuleList"]},
        },
        {
            'format_name': 'snort_logs',
            'display_name': 'Snort IDS/IPS Logs',
            'format_type': 'source',
            'description': 'Snort intrusion detection and prevention system logs',
            'sample_logs': '[**] [1:1000001:1] GPL ICMP_INFO PING [**] [Classification: Misc activity] [Priority: 3] 01/02-10:30:45.123456 192.168.1.100 -> 10.0.0.1 ICMP TTL:64 TOS:0x0 ID:12345 IpLen:20 DgmLen:84',
            'parser_config': {"type": "regex", "regex": r"^\[\*\*\]\s+\[(?P<sid>[^\]]+)\]\s+(?P<message>[^\[]+)\s+\[\*\*\]\s+\[Classification:\s+(?P<classification>[^\]]+)\]\s+\[Priority:\s+(?P<priority>\d+)\]\s+(?P<timestamp>[^\s]+)\s+(?P<src_ip>[^\s]+)\s+->\s+(?P<dst_ip>[^\s]+).*$"},
            'schema': {"fields": ["sid", "message", "classification", "priority", "timestamp", "src_ip", "dst_ip", "protocol"]},
        },
        {
            'format_name': 'suricata_logs',
            'display_name': 'Suricata IDS/IPS Logs',
            'format_type': 'source',
            'description': 'Suricata intrusion detection and prevention system logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123456+0000","flow_id":1234567890,"event_type":"alert","src_ip":"192.168.1.100","src_port":12345,"dest_ip":"10.0.0.1","dest_port":80,"proto":"TCP","alert":{"action":"allowed","gid":1,"signature_id":2000001,"rev":1,"signature":"ET POLICY Suspicious inbound to SQL port 1433","category":"Potentially Bad Traffic","severity":2},"http":{"hostname":"example.com","url":"/api/users","http_user_agent":"Mozilla/5.0"}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "flow_id", "event_type", "src_ip", "src_port", "dest_ip", "dest_port", "proto", "alert", "http"]},
        },
        {
            'format_name': 'imperva_waf',
            'display_name': 'Imperva WAF Logs',
            'format_type': 'source',
            'description': 'Imperva Web Application Firewall logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [Imperva] WAF_BLOCK client_ip="192.168.1.100" host="example.com" uri="/api/users" method="GET" status=403 rule_id="1001" rule_name="SQL Injection" user_agent="Mozilla/5.0"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+client_ip=\"(?P<client_ip>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "client_ip", "host", "uri", "method", "status", "rule_id", "rule_name", "user_agent"]},
        },
        {
            'format_name': 'akamai_kona',
            'display_name': 'Akamai Kona WAF Logs',
            'format_type': 'source',
            'description': 'Akamai Kona Web Application Firewall logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","clientIP":"192.168.1.100","clientRequestHost":"example.com","clientRequestMethod":"GET","clientRequestURI":"/api/users","clientRequestHTTPVersion":"HTTP/1.1","edgeResponseStatus":403,"ruleId":"100000","ruleMessage":"SQL injection attempt","userAgent":"Mozilla/5.0"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "clientIP", "clientRequestHost", "clientRequestMethod", "clientRequestURI", "edgeResponseStatus", "ruleId", "ruleMessage", "userAgent"]},
        },
        # Network Equipment Logs
        {
            'format_name': 'dhcp_logs',
            'display_name': 'DHCP Logs',
            'format_type': 'source',
            'description': 'Dynamic Host Configuration Protocol (DHCP) server logs',
            'sample_logs': '2024-01-02 10:30:45,123 DHCPDISCOVER from 00:11:22:33:44:55 via eth0',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<event>\w+)\s+from\s+(?P<mac_address>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "event", "mac_address", "interface", "ip_address", "hostname"]},
        },
        {
            'format_name': 'dns_logs',
            'display_name': 'DNS Logs',
            'format_type': 'source',
            'description': 'Domain Name System (DNS) query and response logs',
            'sample_logs': '2024-01-02 10:30:45,123 client 192.168.1.100#12345: query: example.com IN A + (192.168.1.1)',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+client\s+(?P<client_ip>[^#]+)#(?P<client_port>\d+):\s+query:\s+(?P<query>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "client_ip", "client_port", "query", "query_type", "response", "response_code"]},
        },
        # Cloud Platform Logs - Additional AWS
        {
            'format_name': 'aws_cloudwatch',
            'display_name': 'AWS CloudWatch Logs',
            'format_type': 'source',
            'description': 'AWS CloudWatch application and system logs',
            'sample_logs': '2024-01-02T10:30:45.123Z INFO [Lambda] RequestId: abc-123-def Function: my-function Message: User logged in',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^\s]+)\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "level", "component", "message", "request_id", "function_name"]},
        },
        {
            'format_name': 'aws_vpc_flow',
            'display_name': 'AWS VPC Flow Logs',
            'format_type': 'source',
            'description': 'AWS VPC Flow Logs for network traffic analysis',
            'sample_logs': '2 123456789012 eni-abc123 192.168.1.100 10.0.0.1 12345 80 6 1024 2048 1704192645 1704192646 ACCEPT OK',
            'parser_config': {"type": "regex", "regex": r"^(?P<version>\d+)\s+(?P<account_id>\d+)\s+(?P<interface_id>[^\s]+)\s+(?P<src_addr>[^\s]+)\s+(?P<dst_addr>[^\s]+)\s+(?P<src_port>\d+)\s+(?P<dst_port>\d+)\s+(?P<protocol>\d+)\s+(?P<packets>\d+)\s+(?P<bytes>\d+)\s+(?P<start>\d+)\s+(?P<end>\d+)\s+(?P<action>[^\s]+)\s+(?P<status>[^\s]+)$"},
            'schema': {"fields": ["version", "account_id", "interface_id", "src_addr", "dst_addr", "src_port", "dst_port", "protocol", "packets", "bytes", "start", "end", "action", "status"]},
        },
        {
            'format_name': 'aws_alb_nlb',
            'display_name': 'AWS ALB/NLB/ELB Logs',
            'format_type': 'source',
            'description': 'AWS Application/Network/Classic Load Balancer access logs',
            'sample_logs': 'http 2024-01-02T10:30:45.123456Z app/my-loadbalancer/50dc6c495c0c9188 192.168.1.100:12345 10.0.0.1:80 0.000 0.001 0.000 200 200 0 1024 "GET http://example.com:80/api/users HTTP/1.1" "Mozilla/5.0" - - arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/my-targets/abc123 "Root=1-abc-123"',
            'parser_config': {"type": "regex", "regex": r"^(?P<type>[^\s]+)\s+(?P<timestamp>[^\s]+)\s+(?P<elb>[^\s]+)\s+(?P<client>[^\s]+)\s+(?P<target>[^\s]+).*$"},
            'schema': {"fields": ["type", "timestamp", "elb", "client", "target", "request_processing_time", "target_processing_time", "response_processing_time", "elb_status_code", "target_status_code", "received_bytes", "sent_bytes", "request", "user_agent"]},
        },
        {
            'format_name': 'aws_guardduty',
            'display_name': 'AWS GuardDuty Findings',
            'format_type': 'source',
            'description': 'AWS GuardDuty threat detection findings',
            'sample_logs': '{"schemaVersion":"2.0","accountId":"123456789012","region":"us-east-1","partition":"aws","id":"abc123-def456-ghi789","arn":"arn:aws:guardduty:us-east-1:123456789012:detector/abc123/finding/def456","type":"Recon:EC2/PortProbeUnprotectedPort","resource":{"instanceDetails":{"instanceId":"i-1234567890abcdef0","instanceType":"t2.micro","launchTime":"2024-01-01T00:00:00Z","imageId":"ami-abc123","imageDescription":"Amazon Linux 2","platform":"Linux"},"resourceType":"Instance"},"service":{"action":{"actionType":"NETWORK_CONNECTION","networkConnectionAction":{"connectionDirection":"INBOUND","remoteIpDetails":{"ipAddressV4":"192.168.1.100","organization":{"asn":"12345","asnOrg":"Example ISP"}},"remotePortDetails":{"port":12345,"portName":"Unknown"},"localPortDetails":{"port":22,"portName":"SSH"},"protocol":"TCP"},"portProbeAction":{"portProbeDetails":[{"localPortDetails":{"port":22,"portName":"SSH"}}]}},"resourceRole":"TARGET","eventFirstSeen":"2024-01-02T10:30:45.123Z","eventLastSeen":"2024-01-02T10:30:45.123Z","count":1},"severity":5,"createdAt":"2024-01-02T10:30:45.123Z","updatedAt":"2024-01-02T10:30:45.123Z","title":"Unprotected port 22 on i-1234567890abcdef0 is being probed"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["schemaVersion", "accountId", "region", "id", "arn", "type", "resource", "service", "severity", "createdAt", "updatedAt", "title"]},
        },
        {
            'format_name': 'aws_security_hub',
            'display_name': 'AWS Security Hub Findings',
            'format_type': 'source',
            'description': 'AWS Security Hub security findings and compliance checks',
            'sample_logs': '{"SchemaVersion":"2018-10-08","Id":"arn:aws:securityhub:us-east-1:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0/S3.1/finding/abc123","ProductArn":"arn:aws:securityhub:us-east-1::product/aws/securityhub","GeneratorId":"aws-foundational-security-best-practices/v/1.0.0/S3.1","AwsAccountId":"123456789012","Types":["Software and Configuration Checks/Industry and Regulatory Standards/AWS-Foundational-Security-Best-Practices"],"FirstObservedAt":"2024-01-02T10:30:45.123Z","CreatedAt":"2024-01-02T10:30:45.123Z","UpdatedAt":"2024-01-02T10:30:45.123Z","Severity":{"Label":"MEDIUM","Original":"MEDIUM"},"Title":"S3.1 S3 bucket should prohibit public read access","Description":"This S3 bucket allows public read access","Remediation":{"Recommendation":{"Text":"Remove public read access from the bucket"}},"Resources":[{"Type":"AwsS3Bucket","Id":"arn:aws:s3:::my-bucket","Partition":"aws","Region":"us-east-1"}],"Compliance":{"Status":"FAILED","RelatedRequirements":["NIST.800-53.r-AC-3"]}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["SchemaVersion", "Id", "ProductArn", "GeneratorId", "AwsAccountId", "Types", "FirstObservedAt", "CreatedAt", "UpdatedAt", "Severity", "Title", "Description", "Remediation", "Resources", "Compliance"]},
        },
        # Cloud Platform Logs - Additional Azure
        {
            'format_name': 'azure_nsg_flow',
            'display_name': 'Azure NSG Flow Logs',
            'format_type': 'source',
            'description': 'Azure Network Security Group flow logs',
            'sample_logs': '{"time":"2024-01-02T10:30:45.123Z","systemId":"abc123","macAddress":"00-11-22-33-44-55","operationName":"NetworkSecurityGroupFlowEvents","resourceId":"/subscriptions/123/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/nsg","time":"2024-01-02T10:30:45.123Z","category":"NetworkSecurityGroupFlowEvent","resourceId":"/subscriptions/123/resourceGroups/rg/providers/Microsoft.Network/networkSecurityGroups/nsg/networkInterfaces/nic","operationName":"NetworkSecurityGroupFlowEvents","properties":{"Version":2,"flows":[{"rule":"DefaultRule_DenyAllInBound","flows":[{"mac":"00-11-22-33-44-55","flowTuples":["1704192645,192.168.1.100,10.0.0.1,12345,80,T,I,A"]}]}]}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["time", "systemId", "macAddress", "operationName", "resourceId", "category", "properties"]},
        },
        {
            'format_name': 'azure_sentinel',
            'display_name': 'Azure Sentinel Detection Logs',
            'format_type': 'source',
            'description': 'Microsoft Azure Sentinel security detection and alert logs',
            'sample_logs': '{"TimeGenerated":"2024-01-02T10:30:45.123Z","AlertName":"Suspicious PowerShell Execution","AlertSeverity":"High","AlertDescription":"PowerShell script execution detected with suspicious patterns","Computer":"hostname","Account":"user","CommandLine":"powershell.exe -EncodedCommand abc123","ProcessId":1234,"ParentProcessId":5678,"SourceIP":"192.168.1.100"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["TimeGenerated", "AlertName", "AlertSeverity", "AlertDescription", "Computer", "Account", "CommandLine", "ProcessId", "ParentProcessId", "SourceIP"]},
        },
        # Cloud Platform Logs - Additional GCP
        {
            'format_name': 'gcp_vpc_flow',
            'display_name': 'GCP VPC Flow Logs',
            'format_type': 'source',
            'description': 'Google Cloud Platform VPC Flow Logs',
            'sample_logs': '{"insertId":"abc123","jsonPayload":{"connection":{"src_ip":"192.168.1.100","src_port":12345,"dest_ip":"10.0.0.1","dest_port":80,"protocol":6},"bytes_sent":1024,"bytes_received":2048,"packets_sent":10,"packets_received":20,"start_time":"2024-01-02T10:30:45.123Z","end_time":"2024-01-02T10:30:46.123Z"},"resource":{"type":"gce_instance","labels":{"instance_id":"1234567890","zone":"us-east1-a","project_id":"my-project"}},"timestamp":"2024-01-02T10:30:45.123Z","severity":"INFO","logName":"projects/my-project/logs/compute.googleapis.com%2Fvpc_flows"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["insertId", "jsonPayload", "resource", "timestamp", "severity", "logName"]},
        },
        {
            'format_name': 'gcp_cloud_armor',
            'display_name': 'GCP Cloud Armor Logs',
            'format_type': 'source',
            'description': 'Google Cloud Armor Web Application Firewall logs',
            'sample_logs': '{"insertId":"abc123","jsonPayload":{"httpRequest":{"requestMethod":"GET","requestUrl":"https://example.com/api/users","requestSize":"1024","status":403,"responseSize":"2048","userAgent":"Mozilla/5.0","remoteIp":"192.168.1.100","serverIp":"10.0.0.1"},"enforcedSecurityPolicy":{"name":"my-policy","outcome":"DENY","priority":1000,"preconfiguredExprIds":["sqli-stable"]}},"resource":{"type":"http_load_balancer","labels":{"backend_service_name":"my-backend","forwarding_rule_name":"my-rule","project_id":"my-project","url_map_name":"my-url-map"}},"timestamp":"2024-01-02T10:30:45.123Z","severity":"WARNING","logName":"projects/my-project/logs/requests"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["insertId", "jsonPayload", "resource", "timestamp", "severity", "logName"]},
        },
        {
            'format_name': 'gcp_threat_detection',
            'display_name': 'GCP Event Threat Detection Logs',
            'format_type': 'source',
            'description': 'Google Cloud Platform Event Threat Detection security logs',
            'sample_logs': '{"insertId":"abc123","jsonPayload":{"@type":"type.googleapis.com/google.cloud.securitycenter.v1.Finding","name":"organizations/123/sources/456/findings/789","parent":"organizations/123/sources/456","resourceName":"//compute.googleapis.com/projects/my-project/zones/us-east1-a/instances/instance-1","state":"ACTIVE","category":"SUSPICIOUS_ACTIVITY","externalUri":"https://console.cloud.google.com/security/command-center/findings/789","sourceProperties":{"DetectionMethod":"ETD","EventTime":"2024-01-02T10:30:45.123Z","FindingClass":"THREAT","Severity":"HIGH"}},"resource":{"type":"gce_instance","labels":{"instance_id":"1234567890","zone":"us-east1-a","project_id":"my-project"}},"timestamp":"2024-01-02T10:30:45.123Z","severity":"ERROR","logName":"projects/my-project/logs/threatdetection.googleapis.com%2Fthreat"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["insertId", "jsonPayload", "resource", "timestamp", "severity", "logName"]},
        },
        # Application Logs
        {
            'format_name': 'api_gateway_kong',
            'display_name': 'Kong API Gateway Logs',
            'format_type': 'source',
            'description': 'Kong API gateway access and error logs',
            'sample_logs': '{"latencies":{"request":10,"kong":5,"proxy":5},"service":{"host":"backend.example.com","created_at":1704192645,"connect_timeout":60000,"id":"abc-123","protocol":"http","name":"my-service","read_timeout":60000,"port":80,"path":"/","updated_at":1704192645,"retries":5,"write_timeout":60000},"request":{"querystring":{},"size":1024,"uri":"/api/users","url":"http://example.com:8000/api/users","headers":{"host":"example.com","user-agent":"Mozilla/5.0","accept":"application/json"},"method":"GET"},"tries":[{"balancer_latency":0,"port":80,"ip":"10.0.0.1"}],"client_ip":"192.168.1.100","upstream_uri":"/api/users","response":{"headers":{"content-length":"2048","via":"kong/2.0.0","connection":"close","access-control-allow-credentials":"true","x-request-id":"req-123","content-type":"application/json"},"status":200,"size":2048},"route":{"id":"def-456","service":{"id":"abc-123"},"name":"my-route","preserve_host":false,"regex_priority":0,"strip_path":true,"paths":["/api"],"created_at":1704192645,"hosts":["example.com"],"updated_at":1704192645,"protocols":["http","https"],"methods":["GET","POST"]},"started_at":1704192645123}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["latencies", "service", "request", "tries", "client_ip", "upstream_uri", "response", "route", "started_at"]},
        },
        {
            'format_name': 'api_gateway_apigee',
            'display_name': 'Apigee API Gateway Logs',
            'format_type': 'source',
            'description': 'Google Apigee API gateway logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","client_id":"client-123","api_product":"my-product","api":"my-api","request_uri":"/api/users","request_method":"GET","request_headers":{"host":"example.com","user-agent":"Mozilla/5.0"},"response_status":200,"response_time_ms":50,"client_ip":"192.168.1.100","user_agent":"Mozilla/5.0"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "client_id", "api_product", "api", "request_uri", "request_method", "request_headers", "response_status", "response_time_ms", "client_ip", "user_agent"]},
        },
        {
            'format_name': 'istio_logs',
            'display_name': 'Istio Service Mesh Logs',
            'format_type': 'source',
            'description': 'Istio service mesh access and telemetry logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","method":"GET","path":"/api/users","protocol":"HTTP/1.1","response_code":200,"response_flags":"-","bytes_received":1024,"bytes_sent":2048,"duration":50,"upstream_service_time":45,"x_forwarded_for":"192.168.1.100","user_agent":"Mozilla/5.0","request_id":"req-123","source_service":"frontend","destination_service":"backend","source_namespace":"default","destination_namespace":"default"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "method", "path", "protocol", "response_code", "response_flags", "bytes_received", "bytes_sent", "duration", "upstream_service_time", "x_forwarded_for", "user_agent", "request_id", "source_service", "destination_service"]},
        },
        {
            'format_name': 'envoy_logs',
            'display_name': 'Envoy Proxy Logs',
            'format_type': 'source',
            'description': 'Envoy proxy access and telemetry logs',
            'sample_logs': '[2024-01-02T10:30:45.123Z] "GET /api/users HTTP/1.1" 200 - 1024 2048 50 45 "-" "Mozilla/5.0" "abc-123-def-456" "backend.example.com" "192.168.1.100:80"',
            'parser_config': {"type": "regex", "regex": r"^\[(?P<timestamp>[^\]]+)\]\s+\"(?P<method>\w+)\s+(?P<path>[^\s]+)\s+(?P<protocol>[^\"]+)\"\s+(?P<status_code>\d+)\s+(?P<response_flags>[^\s]+)\s+(?P<bytes_received>\d+)\s+(?P<bytes_sent>\d+)\s+(?P<duration>\d+)\s+(?P<upstream_service_time>\d+)\s+\"(?P<x_forwarded_for>[^\"]+)\"\s+\"(?P<user_agent>[^\"]+)\"\s+\"(?P<request_id>[^\"]+)\"\s+\"(?P<upstream_host>[^\"]+)\"\s+\"(?P<upstream_cluster>[^\"]+)\"$"},
            'schema': {"fields": ["timestamp", "method", "path", "protocol", "status_code", "response_flags", "bytes_received", "bytes_sent", "duration", "upstream_service_time", "x_forwarded_for", "user_agent", "request_id", "upstream_host", "upstream_cluster"]},
        },
        {
            'format_name': 'django_logs',
            'display_name': 'Django Framework Logs',
            'format_type': 'source',
            'description': 'Django web framework application logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [django.request] GET /api/users 200 [0.05s] user=john.doe ip=192.168.1.100',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<logger>[^\]]+)\]\s+(?P<method>\w+)\s+(?P<path>[^\s]+)\s+(?P<status_code>\d+).*$"},
            'schema': {"fields": ["timestamp", "level", "logger", "method", "path", "status_code", "duration", "user", "ip"]},
        },
        {
            'format_name': 'flask_logs',
            'display_name': 'Flask Framework Logs',
            'format_type': 'source',
            'description': 'Flask web framework application logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [flask.app] 192.168.1.100 - - [02/Jan/2024 10:30:45] "GET /api/users HTTP/1.1" 200 -',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<logger>[^\]]+)\]\s+(?P<client_ip>[^\s]+).*$"},
            'schema': {"fields": ["timestamp", "level", "logger", "client_ip", "method", "path", "status_code"]},
        },
        {
            'format_name': 'spring_boot_logs',
            'display_name': 'Spring Boot Logs',
            'format_type': 'source',
            'description': 'Spring Boot Java application logs',
            'sample_logs': '2024-01-02 10:30:45.123  INFO 12345 --- [http-nio-8080-exec-1] com.example.controller.UserController : GET /api/users - 200 OK',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s+(?P<level>\w+)\s+(?P<pid>\d+)\s+---\s+\[(?P<thread>[^\]]+)\]\s+(?P<logger>[^\s]+)\s+:\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "level", "pid", "thread", "logger", "message", "method", "path", "status_code"]},
        },
        {
            'format_name': 'aws_lambda',
            'display_name': 'AWS Lambda Logs',
            'format_type': 'source',
            'description': 'AWS Lambda serverless function execution logs',
            'sample_logs': 'START RequestId: abc-123-def-456 Version: $LATEST\n2024-01-02T10:30:45.123Z\tabc-123-def-456\tINFO\tUser logged in\nEND RequestId: abc-123-def-456\nREPORT RequestId: abc-123-def-456\tDuration: 100.50 ms\tBilled Duration: 101 ms\tMemory Size: 512 MB\tMax Memory Used: 128 MB',
            'parser_config': {"type": "regex", "regex": r"^(?P<event_type>\w+)\s+RequestId:\s+(?P<request_id>[^\s]+).*$"},
            'schema': {"fields": ["event_type", "request_id", "timestamp", "level", "message", "duration", "memory_size", "max_memory_used"]},
        },
        {
            'format_name': 'gcp_cloud_functions',
            'display_name': 'GCP Cloud Functions Logs',
            'format_type': 'source',
            'description': 'Google Cloud Platform Cloud Functions execution logs',
            'sample_logs': '{"severity":"INFO","timestamp":"2024-01-02T10:30:45.123Z","logging.googleapis.com/labels":{"execution_id":"abc-123"},"message":"User logged in","httpRequest":{"requestMethod":"GET","requestUrl":"https://example.com/api/users","status":200,"responseSize":2048,"userAgent":"Mozilla/5.0","remoteIp":"192.168.1.100"}}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["severity", "timestamp", "logging.googleapis.com/labels", "message", "httpRequest"]},
        },
        # Database Logs
        {
            'format_name': 'mysql_slow_query',
            'display_name': 'MySQL Slow Query Logs',
            'format_type': 'source',
            'description': 'MySQL slow query log entries',
            'sample_logs': '# Time: 2024-01-02T10:30:45.123456Z\n# User@Host: user[user] @ localhost []  Id:   123\n# Query_time: 5.123456  Lock_time: 0.000000 Rows_sent: 100  Rows_examined: 10000\nSET timestamp=1704192645;\nSELECT * FROM users WHERE email LIKE \'%example.com\';',
            'parser_config': {"type": "regex", "regex": r"^#\s+Time:\s+(?P<time>[^\n]+)\n#\s+User@Host:\s+(?P<user>[^\s]+).*Query_time:\s+(?P<query_time>[^\s]+).*$"},
            'schema': {"fields": ["time", "user", "query_time", "lock_time", "rows_sent", "rows_examined", "query"]},
        },
        {
            'format_name': 'postgres_slow_query',
            'display_name': 'PostgreSQL Slow Query Logs',
            'format_type': 'source',
            'description': 'PostgreSQL slow query log entries',
            'sample_logs': '2024-01-02 10:30:45.123 UTC [12345]: [1-1] user=user,db=mydb,app=myapp,client=192.168.1.100 LOG:  duration: 5123.456 ms  statement: SELECT * FROM users WHERE email LIKE \'%example.com\';',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>[^\s]+)\s+\[(?P<pid>\d+)\]:\s+\[(?P<session>[^\]]+)\]\s+user=(?P<user>[^,]+),db=(?P<database>[^,]+).*duration:\s+(?P<duration>[^\s]+)\s+ms\s+statement:\s+(?P<statement>.*)$"},
            'schema': {"fields": ["timestamp", "pid", "session", "user", "database", "duration", "statement"]},
        },
        {
            'format_name': 'sql_server_extended_events',
            'display_name': 'SQL Server Extended Events',
            'format_type': 'source',
            'description': 'Microsoft SQL Server Extended Events logs',
            'sample_logs': '<event name="sql_statement_completed" timestamp="2024-01-02T10:30:45.123Z"><data name="duration"><value>5123456</value></data><data name="cpu_time"><value>1000000</value></data><data name="logical_reads"><value>1000</value></data><data name="statement"><value>SELECT * FROM users WHERE email LIKE \'%example.com\'</value></data></event>',
            'parser_config': {"type": "xml"},
            'schema': {"fields": ["event", "timestamp", "duration", "cpu_time", "logical_reads", "statement"]},
        },
        {
            'format_name': 'mongodb_audit',
            'display_name': 'MongoDB Audit Logs',
            'format_type': 'source',
            'description': 'MongoDB database audit logs',
            'sample_logs': '{"atype":"authCheck","ts":{"$date":"2024-01-02T10:30:45.123Z"},"local":{"ip":"127.0.0.1","port":27017},"remote":{"ip":"192.168.1.100","port":12345},"users":[{"user":"admin","db":"admin"}],"param":{"command":"find","ns":"mydb.users","args":{"find":"users","filter":{"email":{"$regex":"example.com"}}}}},"result":0}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["atype", "ts", "local", "remote", "users", "param", "result"]},
        },
        {
            'format_name': 'redis_logs',
            'display_name': 'Redis Logs',
            'format_type': 'source',
            'description': 'Redis in-memory data store logs',
            'sample_logs': '12345:M 02 Jan 2024 10:30:45.123 * Background saving started by pid 12346\n12345:M 02 Jan 2024 10:30:45.456 * DB saved on disk',
            'parser_config': {"type": "regex", "regex": r"^(?P<pid>\d+):(?P<role>[A-Z])\s+(?P<timestamp>[^\*]+)\*\s+(?P<message>.*)$"},
            'schema': {"fields": ["pid", "role", "timestamp", "message", "level"]},
        },
        {
            'format_name': 'elasticsearch_cluster',
            'display_name': 'Elasticsearch Cluster Logs',
            'format_type': 'source',
            'description': 'Elasticsearch cluster and node logs',
            'sample_logs': '[2024-01-02T10:30:45,123][INFO ][o.e.c.m.MetaDataCreateIndexService] [node-1] [my-index] creating index, cause [api], templates [], shards [1]/[1], mappings []',
            'parser_config': {"type": "regex", "regex": r"^\[(?P<timestamp>[^\]]+)\]\[(?P<level>\w+)\s+\]\[(?P<logger>[^\]]+)\]\s+\[(?P<node>[^\]]+)\]\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "level", "logger", "node", "message", "index", "shard"]},
        },
        # DevOps & CI/CD Logs
        {
            'format_name': 'github_audit',
            'display_name': 'GitHub Audit Logs',
            'format_type': 'source',
            'description': 'GitHub organization and repository audit logs',
            'sample_logs': '{"@timestamp":"2024-01-02T10:30:45.123Z","action":"repo.create","actor":"user","actor_id":12345,"actor_location":{"country_code":"US"},"repo":"example/repo","repo_id":67890,"user":"user","user_id":12345,"org":"example","org_id":11111,"created_at":"2024-01-02T10:30:45.123Z"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["@timestamp", "action", "actor", "actor_id", "actor_location", "repo", "repo_id", "user", "user_id", "org", "org_id", "created_at"]},
        },
        {
            'format_name': 'gitlab_audit',
            'display_name': 'GitLab Audit Logs',
            'format_type': 'source',
            'description': 'GitLab project and group audit logs',
            'sample_logs': '{"time":"2024-01-02T10:30:45.123Z","severity":"INFO","service":"audit","message":"User created repository","user_id":12345,"username":"user","ip_address":"192.168.1.100","project_id":67890,"project_path":"example/repo","action":"repository_created"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["time", "severity", "service", "message", "user_id", "username", "ip_address", "project_id", "project_path", "action"]},
        },
        {
            'format_name': 'jenkins_build',
            'display_name': 'Jenkins Build Logs',
            'format_type': 'source',
            'description': 'Jenkins CI/CD pipeline build logs',
            'sample_logs': '2024-01-02 10:30:45,123 Started by user admin\n2024-01-02 10:30:46,456 Building on master\n2024-01-02 10:30:47,789 [Pipeline] echo\nHello World\n2024-01-02 10:30:48,012 Finished: SUCCESS',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<message>.*)$"},
            'schema': {"fields": ["timestamp", "message", "build_number", "job_name", "status", "duration"]},
        },
        {
            'format_name': 'argocd_logs',
            'display_name': 'ArgoCD / Argo Rollouts Logs',
            'format_type': 'source',
            'description': 'ArgoCD GitOps and Argo Rollouts deployment logs',
            'sample_logs': 'time="2024-01-02T10:30:45Z" level=info msg="Application synced" application=my-app namespace=argocd sync_status=Synced health_status=Healthy',
            'parser_config': {"type": "regex", "regex": r"^time=\"(?P<timestamp>[^\"]+)\"\s+level=(?P<level>\w+)\s+msg=\"(?P<message>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "message", "application", "namespace", "sync_status", "health_status"]},
        },
        {
            'format_name': 'terraform_cloud_audit',
            'display_name': 'Terraform Cloud Audit Logs',
            'format_type': 'source',
            'description': 'HashiCorp Terraform Cloud audit and run logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","version":1,"type":"run","organization":"my-org","workspace":"my-workspace","run_id":"run-abc123","user_id":"user-123","action":"plan","status":"planned","resource_changes":10,"plan_errors":0}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "version", "type", "organization", "workspace", "run_id", "user_id", "action", "status", "resource_changes", "plan_errors"]},
        },
        # MDM / Device Management
        {
            'format_name': 'intune_logs',
            'display_name': 'Microsoft Intune Logs',
            'format_type': 'source',
            'description': 'Microsoft Intune mobile device management logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","eventType":"DeviceCompliance","deviceId":"abc-123-def","deviceName":"DEVICE-01","userId":"user-123","complianceState":"Compliant","policyId":"policy-123","action":"ComplianceCheck","result":"Success"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "eventType", "deviceId", "deviceName", "userId", "complianceState", "policyId", "action", "result"]},
        },
        {
            'format_name': 'jamf_logs',
            'display_name': 'Jamf Logs',
            'format_type': 'source',
            'description': 'Jamf mobile device management logs',
            'sample_logs': '2024-01-02 10:30:45,123 INFO [Jamf] DEVICE_ENROLLED device_id="abc-123" device_name="DEVICE-01" user="user@example.com" serial_number="SN123456" model="MacBook Pro" os_version="14.0"',
            'parser_config': {"type": "regex", "regex": r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+(?P<level>\w+)\s+\[(?P<component>[^\]]+)\]\s+(?P<event>\w+)\s+device_id=\"(?P<device_id>[^\"]+)\".*$"},
            'schema': {"fields": ["timestamp", "level", "component", "event", "device_id", "device_name", "user", "serial_number", "model", "os_version"]},
        },
        {
            'format_name': 'workspace_one_logs',
            'display_name': 'Workspace ONE Logs',
            'format_type': 'source',
            'description': 'VMware Workspace ONE unified endpoint management logs',
            'sample_logs': '{"timestamp":"2024-01-02T10:30:45.123Z","eventType":"DeviceEnrolled","deviceId":"abc-123","deviceName":"DEVICE-01","userId":"user-123","organizationGroupId":"org-123","enrollmentType":"UserEnrollment","platform":"iOS","osVersion":"17.0"}',
            'parser_config': {"type": "json"},
            'schema': {"fields": ["timestamp", "eventType", "deviceId", "deviceName", "userId", "organizationGroupId", "enrollmentType", "platform", "osVersion"]},
        },
    ]
    
    # Insert templates
    
    # Insert templates
    for template in templates:
        # Check if template already exists
        result = connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM log_format_templates 
                WHERE format_name = :format_name
            );
        """), {"format_name": template["format_name"]})
        exists = result.scalar()
        
        if not exists:
            parser_config_json = json.dumps(template['parser_config'])
            schema_json = json.dumps(template['schema'])
            
            connection.execute(text("""
                INSERT INTO log_format_templates (format_name, display_name, format_type, description, sample_logs, parser_config, schema, is_system_template)
                VALUES (
                    :format_name,
                    :display_name,
                    :format_type,
                    :description,
                    :sample_logs,
                    CAST(:parser_config AS jsonb),
                    CAST(:schema AS jsonb),
                    true
                );
            """), {
                "format_name": template["format_name"],
                "display_name": template["display_name"],
                "format_type": template["format_type"],
                "description": template["description"],
                "sample_logs": template["sample_logs"],
                "parser_config": parser_config_json,
                "schema": schema_json,
            })
            connection.commit()


def downgrade() -> None:
    """Remove comprehensive log format templates"""
    connection = op.get_bind()
    connection.execute(text("""
        DELETE FROM log_format_templates 
        WHERE format_name IN (
            'linux_auth_log', 'linux_secure', 'linux_messages', 'linux_kern_log',
            'cron_logs', 'systemd_journal', 'windows_security_events',
            'windows_application_logs', 'windows_system_logs', 'powershell_logs', 'sysmon_logs',
            'pingfed_logs', 'google_workspace_audit', 'keycloak_audit',
            'cyberark_logs', 'beyondtrust_logs', 'vault_audit', 'jita_jit_logs',
            'bastion_ssh_logs', 'sudo_transcripts', 'crowdstrike_falcon',
            'sentinelone_logs', 'carbonblack_logs', 'defender_endpoint', 'tanium_logs',
            'palo_alto_firewall', 'fortinet_fortigate', 'checkpoint_logs',
            'cisco_asa_ftd', 'sonicwall_logs', 'cloudflare_waf', 'aws_waf',
            'snort_logs', 'suricata_logs', 'imperva_waf', 'akamai_kona',
            'dhcp_logs', 'dns_logs', 'aws_cloudwatch', 'aws_vpc_flow',
            'aws_alb_nlb', 'aws_guardduty', 'aws_security_hub', 'azure_nsg_flow',
            'azure_sentinel', 'gcp_vpc_flow', 'gcp_cloud_armor', 'gcp_threat_detection',
            'api_gateway_kong', 'api_gateway_apigee', 'istio_logs', 'envoy_logs',
            'django_logs', 'flask_logs', 'spring_boot_logs', 'aws_lambda',
            'gcp_cloud_functions', 'mysql_slow_query', 'postgres_slow_query',
            'sql_server_extended_events', 'mongodb_audit', 'redis_logs',
            'elasticsearch_cluster', 'github_audit', 'gitlab_audit', 'jenkins_build',
            'argocd_logs', 'terraform_cloud_audit', 'intune_logs', 'jamf_logs',
            'workspace_one_logs'
        );
    """))
    connection.commit()

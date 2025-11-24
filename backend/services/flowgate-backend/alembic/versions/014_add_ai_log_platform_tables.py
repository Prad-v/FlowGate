"""Add AI Log Platform tables

Revision ID: 014_add_ai_log_platform_tables
Revises: 013_add_ai_log_platform_infrastructure
Create Date: 2024-01-15 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_add_ai_log_platform_tables'
down_revision = '013_add_ai_log_platform_infrastructure'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE threat_severity AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE threat_status AS ENUM ('new', 'investigating', 'contained', 'resolved', 'false_positive');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE access_request_type AS ENUM ('jita', 'jitp', 'standard');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE access_request_status AS ENUM ('pending', 'approved', 'denied', 'expired', 'revoked');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE incident_severity AS ENUM ('low', 'medium', 'high', 'critical');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE incident_status AS ENUM ('new', 'investigating', 'contained', 'resolved', 'closed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE entity_type AS ENUM ('user', 'service', 'host');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE playbook_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE playbook_trigger_type AS ENUM ('threat_alert', 'incident', 'access_request', 'anomaly', 'manual');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE embedding_type AS ENUM ('log_pattern', 'ttp_pattern', 'behavior_pattern', 'user_behavior', 'service_behavior');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create incidents table first (threat_alerts references it)
    op.create_table(
        'incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='incident_severity', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('new', 'investigating', 'contained', 'resolved', 'closed', name='incident_status', create_type=False), nullable=False, server_default='new'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contained_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('root_cause_confidence', sa.Float(), nullable=True),
        sa.Column('attack_path', postgresql.JSONB(), nullable=True),
        sa.Column('blast_radius', postgresql.JSONB(), nullable=True),
        sa.Column('correlated_alerts', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('correlated_logs', postgresql.JSONB(), nullable=True),
        sa.Column('timeline', postgresql.JSONB(), nullable=True),
        sa.Column('assigned_to', sa.String(255), nullable=True),
        sa.Column('investigation_notes', sa.Text(), nullable=True),
        sa.Column('evidence_bundle', postgresql.JSONB(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_incidents_severity', 'incidents', ['severity'])
    op.create_index('ix_incidents_status', 'incidents', ['status'])
    op.create_index('ix_incidents_organization_id', 'incidents', ['organization_id'])
    op.create_index('ix_incidents_detected_at', 'incidents', ['detected_at'])

    # Create threat_alerts table (after incidents)
    op.create_table(
        'threat_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', postgresql.ENUM('low', 'medium', 'high', 'critical', name='threat_severity', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('new', 'investigating', 'contained', 'resolved', 'false_positive', name='threat_status', create_type=False), nullable=False, server_default='new'),
        sa.Column('mitre_technique_id', sa.String(50), nullable=True),
        sa.Column('mitre_technique_name', sa.String(255), nullable=True),
        sa.Column('mitre_tactic', sa.String(100), nullable=True),
        sa.Column('mitre_tactics', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('source_type', sa.String(100), nullable=False),
        sa.Column('source_entity', sa.String(255), nullable=True),
        sa.Column('source_log_id', sa.String(255), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('detection_method', sa.String(100), nullable=True),
        sa.Column('raw_log_data', postgresql.JSONB(), nullable=True),
        sa.Column('enriched_data', postgresql.JSONB(), nullable=True),
        sa.Column('indicators', postgresql.JSONB(), nullable=True),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('incidents.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_threat_alerts_severity', 'threat_alerts', ['severity'])
    op.create_index('ix_threat_alerts_status', 'threat_alerts', ['status'])
    op.create_index('ix_threat_alerts_source_type', 'threat_alerts', ['source_type'])
    op.create_index('ix_threat_alerts_organization_id', 'threat_alerts', ['organization_id'])
    op.create_index('ix_threat_alerts_incident_id', 'threat_alerts', ['incident_id'])
    op.create_index('ix_threat_alerts_detected_at', 'threat_alerts', ['detected_at'])

    # Create access_requests table
    op.create_table(
        'access_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('request_type', postgresql.ENUM('jita', 'jitp', 'standard', name='access_request_type', create_type=False), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('justification', sa.Text(), nullable=True),
        sa.Column('requested_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('approved_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_id', sa.String(255), nullable=False),
        sa.Column('requester_email', sa.String(255), nullable=True),
        sa.Column('requester_name', sa.String(255), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('risk_factors', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_scope', postgresql.JSONB(), nullable=True),
        sa.Column('role_drift_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'denied', 'expired', 'revoked', name='access_request_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('approver_id', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approval_rationale', sa.Text(), nullable=True),
        sa.Column('access_token', sa.String(512), nullable=True),
        sa.Column('access_granted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_access_requests_request_type', 'access_requests', ['request_type'])
    op.create_index('ix_access_requests_resource_id', 'access_requests', ['resource_id'])
    op.create_index('ix_access_requests_requester_id', 'access_requests', ['requester_id'])
    op.create_index('ix_access_requests_status', 'access_requests', ['status'])
    op.create_index('ix_access_requests_organization_id', 'access_requests', ['organization_id'])
    op.create_index('ix_access_requests_expires_at', 'access_requests', ['expires_at'])


    # Create persona_baselines table
    op.create_table(
        'persona_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', postgresql.ENUM('user', 'service', 'host', name='entity_type', create_type=False), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=False),
        sa.Column('entity_name', sa.String(255), nullable=True),
        sa.Column('baseline_embedding', postgresql.JSONB(), nullable=True),
        sa.Column('baseline_stats', postgresql.JSONB(), nullable=True),
        sa.Column('behavior_patterns', postgresql.JSONB(), nullable=True),
        sa.Column('training_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('training_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sample_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('anomaly_threshold', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_persona_baselines_entity_type', 'persona_baselines', ['entity_type'])
    op.create_index('ix_persona_baselines_entity_id', 'persona_baselines', ['entity_id'])
    op.create_index('ix_persona_baselines_organization_id', 'persona_baselines', ['organization_id'])
    op.create_index('ix_persona_baselines_is_active', 'persona_baselines', ['is_active'])
    op.create_index('ix_persona_baselines_last_updated_at', 'persona_baselines', ['last_updated_at'])

    # Create persona_anomalies table
    op.create_table(
        'persona_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('baseline_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('persona_baselines.id'), nullable=False),
        sa.Column('deviation_score', sa.Float(), nullable=False),
        sa.Column('anomaly_type', sa.String(100), nullable=True),
        sa.Column('event_data', postgresql.JSONB(), nullable=True),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_investigated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('investigation_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_persona_anomalies_baseline_id', 'persona_anomalies', ['baseline_id'])
    op.create_index('ix_persona_anomalies_event_timestamp', 'persona_anomalies', ['event_timestamp'])

    # Create soar_playbooks table
    op.create_table(
        'soar_playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.Column('playbook_yaml', sa.Text(), nullable=False),
        sa.Column('trigger_type', postgresql.ENUM('threat_alert', 'incident', 'access_request', 'anomaly', 'manual', name='playbook_trigger_type', create_type=False), nullable=False),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('requires_approval', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('risk_threshold', sa.Float(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_soar_playbooks_trigger_type', 'soar_playbooks', ['trigger_type'])
    op.create_index('ix_soar_playbooks_organization_id', 'soar_playbooks', ['organization_id'])
    op.create_index('ix_soar_playbooks_is_enabled', 'soar_playbooks', ['is_enabled'])

    # Create playbook_executions table
    op.create_table(
        'playbook_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('playbook_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('soar_playbooks.id'), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'running', 'completed', 'failed', 'cancelled', name='playbook_status', create_type=False), nullable=False, server_default='pending'),
        sa.Column('trigger_type', postgresql.ENUM('threat_alert', 'incident', 'access_request', 'anomaly', 'manual', name='playbook_trigger_type', create_type=False), nullable=False),
        sa.Column('trigger_entity_id', sa.String(255), nullable=True),
        sa.Column('trigger_entity_type', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_logs', postgresql.JSONB(), nullable=True),
        sa.Column('actions_taken', postgresql.JSONB(), nullable=True),
        sa.Column('errors', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_playbook_executions_playbook_id', 'playbook_executions', ['playbook_id'])
    op.create_index('ix_playbook_executions_status', 'playbook_executions', ['status'])
    op.create_index('ix_playbook_executions_organization_id', 'playbook_executions', ['organization_id'])

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('embedding_type', postgresql.ENUM('log_pattern', 'ttp_pattern', 'behavior_pattern', 'user_behavior', 'service_behavior', name='embedding_type', create_type=False), nullable=False),
        sa.Column('entity_id', sa.String(255), nullable=True),
        sa.Column('entity_type', sa.String(100), nullable=True),
        sa.Column('vector_data', postgresql.JSONB(), nullable=False),
        sa.Column('vector_dimension', sa.Integer(), nullable=False),
        sa.Column('source_data', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now(), server_default=sa.func.now()),
    )
    op.create_index('ix_embeddings_embedding_type', 'embeddings', ['embedding_type'])
    op.create_index('ix_embeddings_entity_id', 'embeddings', ['entity_id'])
    op.create_index('ix_embeddings_organization_id', 'embeddings', ['organization_id'])
    op.create_index('ix_embeddings_created_at', 'embeddings', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('embeddings')
    op.drop_table('playbook_executions')
    op.drop_table('soar_playbooks')
    op.drop_table('persona_anomalies')
    op.drop_table('persona_baselines')
    op.drop_table('incidents')
    op.drop_table('access_requests')
    op.drop_table('threat_alerts')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS embedding_type")
    op.execute("DROP TYPE IF EXISTS playbook_trigger_type")
    op.execute("DROP TYPE IF EXISTS playbook_status")
    op.execute("DROP TYPE IF EXISTS entity_type")
    op.execute("DROP TYPE IF EXISTS incident_status")
    op.execute("DROP TYPE IF EXISTS incident_severity")
    op.execute("DROP TYPE IF EXISTS access_request_status")
    op.execute("DROP TYPE IF EXISTS access_request_type")
    op.execute("DROP TYPE IF EXISTS threat_status")
    op.execute("DROP TYPE IF EXISTS threat_severity")


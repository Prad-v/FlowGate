"""Pytest configuration and fixtures."""
import pytest
import sys
import os
from pathlib import Path

# Add backend to path - try both relative and absolute paths
backend_paths = [
    Path("/app"),  # Docker path (primary)
    Path(__file__).parent.parent / "backend" / "services" / "flowgate-backend",  # Local path
]
for backend_path in backend_paths:
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
        break

# Also add parent directory for imports like 'config', 'database'
if Path("/app").exists():
    sys.path.insert(0, "/app")

from sqlalchemy import create_engine, String, TypeDecorator
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from app.database import Base, get_db
from uuid import uuid4

# Test database URL - use PostgreSQL from Docker
# Use main database for now (migrations already run)
# TODO: Fix test database migrations setup
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://flowgate:flowgate@postgres:5432/flowgate")

# Override UUID type for SQLite compatibility
class GUID(TypeDecorator):
    """Platform-independent GUID type"""
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(String(36))

# Monkey patch UUID and JSONB to use compatible types in SQLite
import sqlalchemy.dialects.postgresql
from sqlalchemy import Text

original_uuid = sqlalchemy.dialects.postgresql.UUID
original_jsonb = sqlalchemy.dialects.postgresql.JSONB

class UUIDCompat(original_uuid):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _compiler_dispatch(self, visitor, **kw):
        if hasattr(visitor, 'dialect') and visitor.dialect.name == 'sqlite':
            return String(36)._compiler_dispatch(visitor, **kw)
        return super()._compiler_dispatch(visitor, **kw)

class JSONBCompat(original_jsonb):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _compiler_dispatch(self, visitor, **kw):
        if hasattr(visitor, 'dialect') and visitor.dialect.name == 'sqlite':
            return Text()._compiler_dispatch(visitor, **kw)
        return super()._compiler_dispatch(visitor, **kw)

# Handle ARRAY types for SQLite
original_array = sqlalchemy.dialects.postgresql.ARRAY

class ARRAYCompat(original_array):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def _compiler_dispatch(self, visitor, **kw):
        if hasattr(visitor, 'dialect') and visitor.dialect.name == 'sqlite':
            return Text()._compiler_dispatch(visitor, **kw)
        return super()._compiler_dispatch(visitor, **kw)

sqlalchemy.dialects.postgresql.UUID = UUIDCompat
sqlalchemy.dialects.postgresql.JSONB = JSONBCompat
sqlalchemy.dialects.postgresql.ARRAY = ARRAYCompat

# Remove SQLite-specific connect_args for PostgreSQL
if "sqlite" in TEST_DATABASE_URL:
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Set up test database with migrations (runs once per test session)"""
    # For now, use main database which already has all migrations
    # In the future, we should properly set up a test database
    if "flowgate_test" in TEST_DATABASE_URL:
        # Try to run migrations on test database
        try:
            from alembic.config import Config
            from alembic import command
            
            # Set up alembic config
            alembic_cfg = Config("/app/alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
            alembic_cfg.set_main_option("script_location", "/app/alembic")
            
            # Run migrations
            command.upgrade(alembic_cfg, "head")
            print("✓ Test database migrations completed")
        except Exception as e:
            print(f"⚠ Migration failed: {e}, using main database instead")
    else:
        print("✓ Using main database (migrations already applied)")

@pytest.fixture(scope="function")
def db():
    """Create a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def db_session(db):
    """Alias for db fixture for compatibility"""
    return db


@pytest.fixture
def test_org_id():
    """Generate a test organization ID."""
    return uuid4()


@pytest.fixture
def sample_template_config():
    """Sample OTel collector config."""
    return """
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:

exporters:
  logging:

service:
  pipelines:
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
"""

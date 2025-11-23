"""Log Format Template model for managing log format templates"""

from sqlalchemy import Column, String, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects import postgresql
import enum
from app.database import Base
from app.models.base import BaseModel


class LogFormatType(str, enum.Enum):
    """Log format type"""
    source = "source"
    destination = "destination"
    both = "both"


class LogFormatTemplate(Base, BaseModel):
    """Log Format Template model for managing log format templates"""

    __tablename__ = "log_format_templates"

    format_name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=False)
    format_type = Column(
        SQLEnum(LogFormatType, name="log_format_type", create_type=True),
        nullable=False,
        index=True
    )
    description = Column(Text, nullable=True)
    sample_logs = Column(Text, nullable=True)  # Example logs in this format
    parser_config = Column(postgresql.JSONB, nullable=True)  # OTel parser configuration
    schema = Column(postgresql.JSONB, nullable=True)  # Expected structure/fields
    is_system_template = Column(Boolean, default=True, nullable=False)


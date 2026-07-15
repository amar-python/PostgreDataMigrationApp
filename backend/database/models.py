"""SQLAlchemy declarative base and ORM models for MEP.

Phase 1 adds MigrationRun and UploadedFile models to track migration
sessions and their associated CSV uploads.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base declarative class for all MEP ORM models."""
    pass


class RunStatus(str, enum.Enum):
    """Lifecycle states for a migration run."""
    CREATED = "created"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    FAILED = "failed"


class MigrationRun(Base):
    """A single migration session — groups uploaded files and tracks status."""

    __tablename__ = "migration_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    environment = Column(String(100), nullable=False, default="development")
    description = Column(Text, nullable=True)
    status = Column(
        Enum(RunStatus, name="run_status"),
        nullable=False,
        default=RunStatus.CREATED,
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship: one run → many uploaded files
    files = relationship(
        "UploadedFile", back_populates="migration_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<MigrationRun id={self.id} name={self.name!r} status={self.status}>"


class UploadedFile(Base):
    """Metadata for a single CSV file uploaded as part of a migration run."""

    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    migration_run_id = Column(
        Integer,
        ForeignKey("migration_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)
    content_type = Column(String(100), nullable=True, default="text/csv")
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    columns = Column(Text, nullable=True)  # JSON string of column names
    uploaded_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationship back to the parent run
    migration_run = relationship("MigrationRun", back_populates="files")

    def __repr__(self) -> str:
        return f"<UploadedFile id={self.id} filename={self.original_filename!r}>"

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
    """Lifecycle states for a migration run.

    State machine::

        CREATED ──▶ UPLOADING ──▶ VALIDATING ──▶ READY ──▶ MIGRATING ──▶ COMPLETED
           │            │             │            │           │
           └────────────┴─────────────┴────────────┴───────────┴──▶ ERROR / FAILED

    ``ERROR`` marks a run whose upload/validation broke mid-way (recoverable by
    re-uploading or re-validating); ``FAILED`` marks a migration execution that
    ran and did not succeed.
    """
    CREATED = "created"
    UPLOADING = "uploading"
    VALIDATING = "validating"
    READY = "ready"
    MIGRATING = "migrating"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class InvalidStateTransition(Exception):
    """Raised when a migration run is moved to a state it cannot reach."""


# Explicit allowed transitions. Same-state transitions are always allowed
# (idempotent updates, e.g. uploading a second file while UPLOADING).
ALLOWED_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.CREATED: frozenset({
        RunStatus.UPLOADING, RunStatus.VALIDATING, RunStatus.MIGRATING, RunStatus.ERROR,
    }),
    RunStatus.UPLOADING: frozenset({
        RunStatus.VALIDATING, RunStatus.READY, RunStatus.MIGRATING,
        RunStatus.ERROR, RunStatus.CREATED,
    }),
    RunStatus.VALIDATING: frozenset({
        RunStatus.READY, RunStatus.ERROR, RunStatus.CREATED,
    }),
    RunStatus.READY: frozenset({
        RunStatus.UPLOADING, RunStatus.VALIDATING, RunStatus.MIGRATING, RunStatus.ERROR,
    }),
    RunStatus.MIGRATING: frozenset({
        RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.ERROR, RunStatus.CREATED,
    }),
    RunStatus.COMPLETED: frozenset({
        RunStatus.VALIDATING, RunStatus.MIGRATING, RunStatus.ERROR,
    }),
    RunStatus.FAILED: frozenset({
        RunStatus.UPLOADING, RunStatus.VALIDATING, RunStatus.MIGRATING, RunStatus.ERROR,
    }),
    RunStatus.ERROR: frozenset({
        RunStatus.CREATED, RunStatus.UPLOADING, RunStatus.VALIDATING, RunStatus.MIGRATING,
    }),
}


def can_transition(current: RunStatus, target: RunStatus) -> bool:
    """Return True when ``current`` → ``target`` is a legal state change."""
    if current == target:
        return True
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


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

    def transition_to(self, target: "RunStatus") -> None:
        """Move the run to ``target``, enforcing the lifecycle state machine.

        Raises ``InvalidStateTransition`` for illegal moves (e.g. COMPLETED →
        UPLOADING) so bugs surface immediately instead of corrupting run state.
        """
        current = self.status if isinstance(self.status, RunStatus) else RunStatus(self.status)
        if not can_transition(current, target):
            raise InvalidStateTransition(
                f"Migration run {self.id}: illegal transition "
                f"{current.value!r} → {target.value!r}"
            )
        self.status = target

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

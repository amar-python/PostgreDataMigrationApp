"""Pydantic schemas for the MEP REST API.

These models define request bodies, response payloads, and validation rules.
They are intentionally separate from the SQLAlchemy ORM models in
``database/models.py``.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Migration Run
# ---------------------------------------------------------------------------

class MigrationRunCreate(BaseModel):
    """Request body for creating a new migration run."""
    name: str = Field(..., min_length=1, max_length=255, examples=["Q3 Customer Migration"])
    environment: str = Field("development", max_length=100, examples=["development", "staging", "production"])
    description: Optional[str] = Field(None, examples=["Migrate Q3 customer data from legacy CRM"])


class MigrationRunResponse(BaseModel):
    """Response payload representing a migration run."""
    id: int
    name: str
    environment: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    file_count: int = 0
    total_size: int = 0

    model_config = {"from_attributes": True}


class MigrationRunListResponse(BaseModel):
    """Paginated list of migration runs."""
    runs: list["MigrationRunResponse"]
    total: int


# ---------------------------------------------------------------------------
# Uploaded File
# ---------------------------------------------------------------------------

class UploadedFileResponse(BaseModel):
    """Response payload representing a single uploaded CSV file."""
    id: int
    migration_run_id: int
    original_filename: str
    stored_filename: str
    file_size: int
    content_type: Optional[str]
    row_count: Optional[int]
    column_count: Optional[int]
    columns: Optional[str]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class UploadedFileListResponse(BaseModel):
    """List of uploaded files for a migration run."""
    files: list[UploadedFileResponse]
    total: int


class DeleteResponse(BaseModel):
    """Generic deletion confirmation."""
    detail: str
    id: int


# ---------------------------------------------------------------------------
# Schema Discovery & Validation
# ---------------------------------------------------------------------------

class ColumnSchema(BaseModel):
    """Inferred schema for a single CSV column."""
    name: str
    inferred_type: str
    nullable: bool
    unique: bool
    sample_values: list[str]
    null_count: int
    total_count: int


class ValidationIssue(BaseModel):
    """A single validation finding."""
    severity: str  # error | warning | info
    check: str
    column: Optional[str]
    message: str


class FileValidationResult(BaseModel):
    """Schema + validation results for one uploaded file."""
    file_id: int
    filename: str
    schema_info: list[ColumnSchema] = Field(default_factory=list, alias="schema")
    issues: list[ValidationIssue]

    model_config = {"populate_by_name": True}


class ValidationSummary(BaseModel):
    """Aggregate counts across all files."""
    total_files: int
    errors: int
    warnings: int
    passed: bool


class ValidationResponse(BaseModel):
    """Full validation response for a migration run."""
    run_id: int
    status: str
    files: list[FileValidationResult]
    summary: ValidationSummary


# ---------------------------------------------------------------------------
# Migration Execution
# ---------------------------------------------------------------------------

class MigrationExecuteResponse(BaseModel):
    """Response after executing migration."""
    run_id: int
    status: str
    files: list[dict]
    summary: dict


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

class EvaluationResponse(BaseModel):
    """Evaluation quality-check response."""
    run_id: int
    status: str
    files: list[dict]
    summary: dict


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class ReportResponse(BaseModel):
    """Report metadata."""
    run_id: int
    format: str
    download_url: str


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardStats(BaseModel):
    """Dashboard summary statistics."""
    total_runs: int
    runs_by_status: dict[str, int]
    total_files: int
    total_rows: int
    total_size: int
    recent_runs: list[MigrationRunResponse]

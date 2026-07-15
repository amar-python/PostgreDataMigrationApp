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

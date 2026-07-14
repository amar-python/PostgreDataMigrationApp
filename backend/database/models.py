"""SQLAlchemy declarative base and ORM models for MEP.

This module currently only exposes the declarative ``Base``. MEP metadata
models (e.g. ``MigrationRun``, ``UploadedFile``) will be added in later steps.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarative class for all MEP ORM models."""

    pass

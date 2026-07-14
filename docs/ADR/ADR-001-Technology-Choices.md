# ADR-001: Technology Choices

- **Status:** Accepted
- **Date:** 2026-07-14

## Context

MEP needs a web frontend, an API layer, and a relational datastore to wrap the
existing CSV → PostgreSQL migration engine. We need a stack that is productive,
widely supported, and a good fit for the engine's existing PostgreSQL focus.

## Decision

- **Frontend: React + TypeScript + Material UI (MUI).**
  React is the dominant SPA framework with a deep ecosystem and hiring pool.
  TypeScript adds type safety. MUI provides a mature component library that
  lets us mirror the Azure Portal look-and-feel quickly.
- **Backend: FastAPI (Python 3.11).**
  The migration engine is already Python/Bash, so a Python API keeps one
  language for backend logic and enables direct reuse of engine code. FastAPI
  gives async performance, Pydantic validation, and automatic OpenAPI docs.
- **Database: PostgreSQL 15.**
  The engine's primary, best-tested target is PostgreSQL, so using it for
  application data keeps operational tooling and expertise consistent.

## Consequences

- One backend language (Python) across API and engine reduces context switching.
- Automatic OpenAPI docs and typed frontend contracts speed up development.
- MUI accelerates a polished, Azure-style UI at the cost of a heavier bundle.
- Committing to PostgreSQL is low-risk given the engine's existing reliance on it.

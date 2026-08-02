# Pull Request

## Summary

<!-- What does this PR change and why? Link related issues. -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / code quality
- [ ] CI / tooling
- [ ] Documentation

## Checklist

### Tests Added

- [ ] New/changed behaviour is covered by unit tests
- [ ] Full backend test suite passes locally (`pytest backend/tests/`)
- [ ] Legacy migration tests still pass where applicable
      (`pytest backend/migration/tests/`)

### Verified Workflow Paths

- [ ] I ran the workflow path verifier and it passed:
      `python3 tools/verify_workflow_paths.py`
      (verifies every file/script referenced by CI workflows exists)
- [ ] Any moved/renamed files are updated in workflows, scripts
      (`scripts/`, `preflight.*`), and docs

### Safety & Security

- [ ] No new `# nosec` / `# noqa` suppressions — or each new suppression is
      documented in `docs/security/Rationale.md`
- [ ] No secrets, credentials, or internal paths added to code or logs
- [ ] Shell scripts validate their inputs (env names, table names, paths)

### API & Data

- [ ] New/changed endpoints declare a Pydantic `response_model`
- [ ] Database state transitions follow the `RunStatus` lifecycle
      (`ALLOWED_TRANSITIONS` in `backend/database/models.py`)

## Screenshots / Output

<!-- Test runs, CLI output, or UI screenshots where relevant. -->

## Notes for Reviewers

<!-- Anything reviewers should pay special attention to. -->

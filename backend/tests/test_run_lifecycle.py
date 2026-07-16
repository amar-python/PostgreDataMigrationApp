"""Tests for the MigrationRun lifecycle state machine.

Verifies the explicit transition rules (CREATED → UPLOADING → VALIDATING →
READY → MIGRATING → COMPLETED, with ERROR/FAILED escape hatches), that
illegal transitions raise, and that a mid-way upload failure flags the run
as ERROR.
"""
import io
from unittest.mock import patch

import pytest

from database.models import (
    InvalidStateTransition,
    MigrationRun,
    RunStatus,
    can_transition,
)


# ---------------------------------------------------------------------------
# Pure transition-rule tests
# ---------------------------------------------------------------------------

class TestTransitionRules:

    @pytest.mark.parametrize("current,target", [
        (RunStatus.CREATED, RunStatus.UPLOADING),
        (RunStatus.UPLOADING, RunStatus.VALIDATING),
        (RunStatus.VALIDATING, RunStatus.READY),
        (RunStatus.READY, RunStatus.MIGRATING),
        (RunStatus.MIGRATING, RunStatus.COMPLETED),
        (RunStatus.MIGRATING, RunStatus.FAILED),
        (RunStatus.VALIDATING, RunStatus.ERROR),
        (RunStatus.UPLOADING, RunStatus.ERROR),
        (RunStatus.ERROR, RunStatus.UPLOADING),   # recover by re-uploading
        (RunStatus.ERROR, RunStatus.VALIDATING),  # recover by re-validating
        (RunStatus.FAILED, RunStatus.MIGRATING),  # retry execution
        (RunStatus.READY, RunStatus.UPLOADING),   # add more files
    ])
    def test_legal_transitions(self, current, target):
        assert can_transition(current, target)

    @pytest.mark.parametrize("current,target", [
        (RunStatus.COMPLETED, RunStatus.UPLOADING),
        (RunStatus.COMPLETED, RunStatus.CREATED),
        (RunStatus.COMPLETED, RunStatus.READY),
        (RunStatus.CREATED, RunStatus.COMPLETED),
        (RunStatus.CREATED, RunStatus.READY),
        (RunStatus.CREATED, RunStatus.FAILED),
        (RunStatus.VALIDATING, RunStatus.MIGRATING),
        (RunStatus.VALIDATING, RunStatus.COMPLETED),
        (RunStatus.ERROR, RunStatus.COMPLETED),
        (RunStatus.ERROR, RunStatus.READY),
    ])
    def test_illegal_transitions(self, current, target):
        assert not can_transition(current, target)

    @pytest.mark.parametrize("state", list(RunStatus))
    def test_same_state_transition_is_always_legal(self, state):
        assert can_transition(state, state)

    def test_every_state_is_covered_by_the_map(self):
        from database.models import ALLOWED_TRANSITIONS
        assert set(ALLOWED_TRANSITIONS) == set(RunStatus)


# ---------------------------------------------------------------------------
# transition_to() on the ORM model
# ---------------------------------------------------------------------------

class TestTransitionTo:

    def test_transition_to_updates_status(self):
        run = MigrationRun(name="t", status=RunStatus.CREATED)
        run.transition_to(RunStatus.UPLOADING)
        assert run.status == RunStatus.UPLOADING

    def test_illegal_transition_raises(self):
        run = MigrationRun(name="t", status=RunStatus.COMPLETED)
        with pytest.raises(InvalidStateTransition):
            run.transition_to(RunStatus.UPLOADING)

    def test_illegal_transition_leaves_status_untouched(self):
        run = MigrationRun(name="t", status=RunStatus.COMPLETED)
        with pytest.raises(InvalidStateTransition):
            run.transition_to(RunStatus.CREATED)
        assert run.status == RunStatus.COMPLETED


# ---------------------------------------------------------------------------
# API-level lifecycle behaviour
# ---------------------------------------------------------------------------

class TestLifecycleViaApi:

    def _create_run(self, client) -> int:
        return client.post("/api/migrations", json={"name": "Lifecycle"}).json()["id"]

    def _upload(self, client, run_id, content=b"id,name\n1,Alice\n"):
        return client.post(
            f"/api/migrations/{run_id}/files",
            files=[("files", ("data.csv", io.BytesIO(content), "text/csv"))],
        )

    def test_upload_moves_run_to_uploading(self, client):
        run_id = self._create_run(client)
        assert self._upload(client, run_id).status_code == 201
        assert client.get(f"/api/migrations/{run_id}").json()["status"] == "uploading"

    def test_successful_validation_moves_run_to_ready(self, client):
        run_id = self._create_run(client)
        self._upload(client, run_id)
        resp = client.post(f"/api/migrations/{run_id}/validate")
        assert resp.status_code == 200
        assert resp.json()["summary"]["passed"] is True
        assert client.get(f"/api/migrations/{run_id}").json()["status"] == "ready"

    def test_failed_upload_flags_run_as_error(self, client):
        """If the upload dies mid-way, the run must be flagged ERROR."""
        run_id = self._create_run(client)
        with patch(
            "services.migration_service._ensure_upload_dir",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(OSError):
                self._upload(client, run_id)
        assert client.get(f"/api/migrations/{run_id}").json()["status"] == "error"

    def test_run_recovers_from_error_by_reuploading(self, client):
        run_id = self._create_run(client)
        with patch(
            "services.migration_service._ensure_upload_dir",
            side_effect=OSError("disk full"),
        ):
            with pytest.raises(OSError):
                self._upload(client, run_id)
        # Retry without the failure — run should move back to UPLOADING
        assert self._upload(client, run_id).status_code == 201
        assert client.get(f"/api/migrations/{run_id}").json()["status"] == "uploading"

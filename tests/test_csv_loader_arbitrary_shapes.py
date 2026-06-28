"""End-to-end regression for the 'any CSV file' guarantee.

Generates CSV files of varying shapes (column count × row count), runs them
through build/csv_loader.sh into a live PostgreSQL instance, and asserts the
auto-created table contains the right number of rows. Complements the
offline Tier P scenarios in evals/datasets/tier_p/ — those exercise the
validator only; these exercise the full validator → loader → DB pipeline.

Skipped automatically when PostgreSQL is not reachable.
"""
import csv
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT       = Path(__file__).resolve().parents[1]
LOADER     = ROOT / "build" / "csv_loader.sh"
UTILISE    = ROOT / "build" / "csv_utilise.sh"
BUILD_DIR  = ROOT / "build"


def _can_connect_pg() -> bool:
    if not shutil.which("psql"):
        return False
    try:
        r = subprocess.run(
            ["psql", "-tA", "-c", "SELECT 1"],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, "PGUSER": os.environ.get("PGUSER", "postgres")},
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


_PG_AVAILABLE = _can_connect_pg()
_CONFIG_PRESENT = (BUILD_DIR / "config.local.env").exists()
_SKIP_REASON = (
    "PostgreSQL not reachable" if not _PG_AVAILABLE
    else "build/config.local.env not present — run ./build/setup.sh"
)


def _write_csv(path: Path, n_cols: int, n_rows: int) -> None:
    header = [f"col_{i}" for i in range(n_cols)]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in range(n_rows):
            w.writerow([f"r{r}c{i}" for i in range(n_cols)])


@unittest.skipUnless(_PG_AVAILABLE and _CONFIG_PRESENT, _SKIP_REASON)
class CsvLoaderArbitraryShapes(unittest.TestCase):
    """Loads CSVs of varying shape into Postgres and verifies row counts."""

    SHAPES = [
        ("tiny",    2, 3),
        ("medium", 10, 50),
        ("skinny",  1, 100),
    ]

    def _run_loader_and_count(self, n_cols: int, n_rows: int, label: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # Use a unique table name so parallel runs don't collide.
            table = f"arb_{label}_{os.getpid()}"
            csv_path = Path(tmp) / f"{table}.csv"
            _write_csv(csv_path, n_cols, n_rows)

            load = subprocess.run(
                ["bash", str(LOADER), str(csv_path), "--env", "dev"],
                capture_output=True, text=True, cwd=ROOT,
            )
            self.assertEqual(
                load.returncode, 0,
                f"Loader failed for {label}: stdout={load.stdout[-500:]} stderr={load.stderr[-500:]}",
            )

            try:
                # Verify via csv_utilise.sh describe (also asserts marker columns present).
                describe = subprocess.run(
                    ["bash", str(UTILISE), "describe", table, "--env", "dev"],
                    capture_output=True, text=True, cwd=ROOT,
                )
                self.assertEqual(describe.returncode, 0, describe.stderr)
                self.assertIn(f"Row count: {n_rows}", describe.stdout)
            finally:
                # Always drop the table — keep dev clean.
                subprocess.run(
                    ["bash", str(UTILISE), "drop", table, "--yes", "--env", "dev"],
                    capture_output=True, text=True, cwd=ROOT,
                )

    def test_shape_tiny(self):
        self._run_loader_and_count(2, 3, "tiny")

    def test_shape_medium(self):
        self._run_loader_and_count(10, 50, "medium")

    def test_shape_skinny(self):
        self._run_loader_and_count(1, 100, "skinny")


if __name__ == "__main__":
    unittest.main()

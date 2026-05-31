import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / "evals" / "runner.py"

spec = importlib.util.spec_from_file_location("evals_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class EvalsRunnerTests(unittest.TestCase):
    def test_load_expected_returns_none_for_missing_scenario(self):
        self.assertIsNone(runner._load_expected("p", "does_not_exist"))

    def test_discover_scenarios_filters_only_requested_name(self):
        scenarios = runner.discover_scenarios("p", "01_happy_path")
        self.assertEqual([p.name for p in scenarios], ["01_happy_path"])

    def test_tier_p_reports_unknown_runner_action_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            scenario = tmp_path / "01_bad_action"
            expected_dir = tmp_path / "expected" / "tier_p"
            scenario.mkdir()
            expected_dir.mkdir(parents=True)
            (expected_dir / "01_bad_action.json").write_text(
                '{"scenario":"01_bad_action","runner_action":"nope","expected":{}}',
                encoding="utf-8",
            )

            with mock.patch.object(runner, "EXPECTED_DIR", tmp_path / "expected"):
                result = runner.run_tier_p_scenario(scenario)

        self.assertFalse(result.passed)
        self.assertIn("Unknown runner_action", result.errors[0])

    def test_tier_p_generated_invalid_utf8_fails_cleanly(self):
        scenario = PROJECT_ROOT / "evals" / "datasets" / "tier_p" / "23_invalid_utf8_bytes"
        result = runner.run_tier_p_scenario(scenario)

        self.assertTrue(result.passed, result.errors)
        self.assertEqual(result.actual["exit_code"], 1)
        self.assertIn("Unexpected error", result.actual["stderr"])
        self.assertNotIn("Traceback", result.actual["stderr"])

    def test_tier_i_skips_when_postgresql_is_unavailable(self):
        scenario = PROJECT_ROOT / "evals" / "datasets" / "tier_i" / "01_deploy_dev_twice"

        with mock.patch.object(runner, "_can_connect_pg", return_value=False):
            result = runner.run_tier_i_scenario(scenario)

        self.assertTrue(result.skipped)
        self.assertFalse(result.passed)
        self.assertIn("PostgreSQL not reachable", result.errors[0])

    def test_count_dev_rows_records_none_for_failed_count_query(self):
        fake_cp = mock.Mock(returncode=1, stdout="", stderr="relation missing")

        with mock.patch.object(runner.subprocess, "run", return_value=fake_cp):
            counts = runner._count_dev_rows()

        self.assertEqual(set(counts), set(runner._DEV_SEED_TABLES))
        self.assertTrue(all(value is None for value in counts.values()))

    def test_have_psql_uses_path_lookup(self):
        with mock.patch.object(shutil, "which", return_value=None):
            self.assertFalse(runner._have_psql())


if __name__ == "__main__":
    unittest.main()

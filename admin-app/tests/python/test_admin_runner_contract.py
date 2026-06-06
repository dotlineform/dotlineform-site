#!/usr/bin/env python3
"""Focused tests for the Admin-owned check runner."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "admin-app" / "commands" / "run_checks.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("admin_run_checks", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load Admin run_checks.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_admin_runner_uses_admin_output_root() -> None:
    runner = load_runner_module()

    assert runner.RUNS_DIR == REPO_ROOT / "var" / "admin" / "test-runs"


def test_admin_runner_expands_admin_smoke_profile_without_studio_risk_route() -> None:
    runner = load_runner_module()

    commands = runner.expand_profiles(["admin-smoke", "studio-smoke"])
    names = [command.name for command in commands]
    argv_text = "\n".join(" ".join(command.argv) for command in commands)

    assert "admin-home-route-smoke" in names
    assert "admin-operations-routes-smoke" in names
    assert "local-studio-risk-route-smoke" not in names
    assert "studio/tests/smoke/local_studio_app_risk_route.py" not in argv_text


def test_admin_runner_writes_summary_paths_under_admin_root(tmp_path, monkeypatch) -> None:
    runner = load_runner_module()
    runs_dir = REPO_ROOT / "var" / "admin" / "test-runs" / "pytest-runner-contract"
    if runs_dir.exists():
        shutil.rmtree(runs_dir)
    monkeypatch.setattr(runner, "RUNS_DIR", runs_dir)

    try:
        run_dir = runner.create_run_dir("runner-contract")
        result = {
            "name": "sample",
            "description": "sample command",
            "command": [sys.executable, "-c", "pass"],
            "exit_code": 0,
            "duration_seconds": 0.0,
            "log": "var/admin/test-runs/pytest-runner-contract/runner-contract/001-sample.log",
        }
        runner.write_summaries(run_dir, ["quick"], [result])

        payload = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
        assert payload["status"] == "passed"
        assert payload["run_dir"] == "var/admin/test-runs/pytest-runner-contract/runner-contract"
        assert "var/admin/test-runs/pytest-runner-contract/runner-contract/001-sample.log" in (run_dir / "summary.md").read_text(encoding="utf-8")
    finally:
        if runs_dir.exists():
            shutil.rmtree(runs_dir)


def test_admin_runner_executes_representative_app_local_pytest(tmp_path) -> None:
    runner = load_runner_module()
    log_dir = REPO_ROOT / "var" / "admin" / "test-runs" / "pytest-runner-command"
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True)
    log_path = log_dir / "admin-pytest.log"
    command = runner.CheckCommand(
        "representative-admin-pytest",
        runner.pytest_argv("admin-app/tests/python/test_admin_ui_catalogue.py"),
        "Run one Admin app-local pytest target.",
    )

    try:
        result = runner.run_command(command, log_path)

        assert result["exit_code"] == 0
        assert "admin-app/tests/python/test_admin_ui_catalogue.py" in log_path.read_text(encoding="utf-8")
    finally:
        if log_dir.exists():
            shutil.rmtree(log_dir)

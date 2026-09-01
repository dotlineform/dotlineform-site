#!/usr/bin/env python3
"""Focused checks for Catalogue build service subprocess boundaries."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = REPO_ROOT / "studio/services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio/shared/python"
for candidate in (SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from catalogue import catalogue_build_service as build_service  # noqa: E402


def test_search_rebuild_failure_logs_diagnostic_but_raises_safe_message(
    tmp_path: Path,
    monkeypatch,
) -> None:
    logged: list[tuple[Path, str, dict[str, object]]] = []
    monkeypatch.setattr(
        build_service.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=1,
            stdout="",
            stderr="Traceback: /private/source/path\nModuleNotFoundError: private_module\n",
        ),
    )
    monkeypatch.setattr(
        build_service,
        "log_event",
        lambda repo_root, event, details: logged.append((repo_root, event, details)),
    )

    with pytest.raises(RuntimeError, match=r"^Catalogue search rebuild failed\.$"):
        build_service.run_catalogue_search_rebuild(tmp_path, write=True)

    assert logged == [
        (
            tmp_path,
            "catalogue_search_rebuild_failed",
            {
                "ok": False,
                "exit_code": 1,
                "stdout_tail": "",
                "stderr_tail": "Traceback: /private/source/path\nModuleNotFoundError: private_module",
            },
        )
    ]

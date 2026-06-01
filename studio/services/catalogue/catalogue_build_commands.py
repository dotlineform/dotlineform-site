"""Catalogue scoped-build command construction and step result helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence


def build_generate_command(
    repo_root: Path,
    source_dir: Path,
    scope: Mapping[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "studio" / "services" / "catalogue" / "generate_work_pages.py"),
        "--internal-json-source-run",
        "--source-dir",
        str(source_dir),
        "--work-ids",
        ",".join(str(work_id) for work_id in scope["work_ids"]),
    ]
    series_ids = [str(series_id) for series_id in scope.get("series_ids", [])]
    if series_ids:
        cmd += ["--series-ids", ",".join(series_ids)]
    for artifact in scope.get("generate_only", []):
        cmd += ["--only", str(artifact)]
    if write:
        cmd.append("--write")
    if refresh_published:
        cmd.append("--refresh-published")
    if force:
        cmd.append("--force")
    return cmd


def build_generate_moment_command(
    repo_root: Path,
    source_dir: Path,
    scope: Mapping[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "studio" / "services" / "catalogue" / "generate_work_pages.py"),
        "--internal-json-source-run",
        "--source-dir",
        str(source_dir),
        "--only",
        "moments",
        "--moment-ids",
        ",".join(str(moment_id) for moment_id in scope["moment_ids"]),
    ]
    if write:
        cmd.append("--write")
    if refresh_published:
        cmd.append("--refresh-published")
    if force:
        cmd.append("--force")
    return cmd


def build_search_command(repo_root: Path, *, write: bool, force: bool, env: Mapping[str, str] | None = None) -> list[str]:
    _ = env
    cmd = [
        sys.executable,
        str(repo_root / "studio" / "services" / "catalogue" / "search" / "build_search.py"),
        "--scope",
        "catalogue",
    ]
    if write:
        cmd.append("--write")
    if force:
        cmd.append("--force")
    return cmd


def tail_output(value: str, *, limit: int = 8) -> str:
    if not value:
        return ""
    return "\n".join(value.strip().splitlines()[-limit:])


def normalize_subprocess_step(
    label: str,
    command: Sequence[str],
    *,
    returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> Dict[str, Any]:
    return {
        "label": label,
        "command": list(command),
        "exit_code": int(returncode),
        "stdout_tail": tail_output(stdout),
        "stderr_tail": tail_output(stderr),
    }


def step_failure_message(label: str, step: Mapping[str, Any]) -> str:
    stderr = str(step.get("stderr_tail") or "").strip()
    stdout = str(step.get("stdout_tail") or "").strip()
    if stderr:
        return stderr
    if stdout:
        return stdout
    return f"{label} failed with exit code {int(step.get('exit_code', 1))}"

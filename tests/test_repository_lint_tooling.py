"""Contract tests for repository-owned lint target resolution."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "tooling" / "lint" / "run_lint.py"
ADMIN_TARGET_MAP_PATH = REPO_ROOT / "admin-app" / "checks" / "config" / "admin-checks.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("repository_lint_runner", RUNNER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load repository lint runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_target_configuration_exposes_application_boundaries() -> None:
    runner = load_runner()
    config = runner.load_targets()

    assert set(config["scopes"]) == {
        "admin",
        "docs-viewer",
        "public-site",
        "shared",
        "site-tools",
        "studio",
        "tests",
    }
    assert config["scopes"]["studio"]["python"]
    assert config["scopes"]["studio"]["javascript"]
    assert config["scopes"]["shared"]["javascript"] == ["shared/frontend/js"]


def test_application_lint_roots_remain_visible_to_the_admin_target_map() -> None:
    """Keep inventory ownership aligned without deriving lint runtime settings."""
    runner = load_runner()
    lint_scopes = runner.load_targets()["scopes"]
    admin_scopes = json.loads(ADMIN_TARGET_MAP_PATH.read_text(encoding="utf-8"))["scopes"]
    ownership = {
        "admin": "admin",
        "docs-viewer": "docs-viewer",
        "public-site": "public-site",
        "site-tools": "public-site",
        "studio": "studio",
    }

    for lint_scope_id, admin_scope_id in ownership.items():
        includes = tuple(admin_scopes[admin_scope_id]["include"])
        roots = (
            *lint_scopes[lint_scope_id]["python"],
            *lint_scopes[lint_scope_id]["javascript"],
        )
        assert roots
        assert all(
            any(root.startswith(include) or include.startswith(f"{root}/") for include in includes)
            for root in roots
        )

    all_admin_includes = {
        include
        for scope in admin_scopes.values()
        for include in scope["include"]
    }
    assert not any("shared/frontend/js".startswith(include) for include in all_admin_includes)


def test_explicit_target_resolution_rejects_missing_and_excluded_source() -> None:
    runner = load_runner()
    exclusions = tuple(runner.load_targets()["exclude"])

    with pytest.raises(runner.LintTargetError, match="does not exist"):
        runner.candidate_files(
            ["studio/not-present.py"],
            language="python",
            exclusions=exclusions,
        )
    with pytest.raises(runner.LintTargetError, match="No eligible python source"):
        runner.candidate_files(
            ["processing"],
            language="python",
            exclusions=exclusions,
        )


def test_explicit_target_resolution_returns_only_requested_language() -> None:
    runner = load_runner()
    exclusions = tuple(runner.load_targets()["exclude"])

    files = runner.candidate_files(
        ["shared/frontend/js"],
        language="javascript",
        exclusions=exclusions,
    )

    assert files
    assert all(path.startswith("shared/frontend/js/") for path in files)
    assert all(path.endswith(".js") for path in files)


def run_lint(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER_PATH), *arguments],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def test_runner_rejects_empty_and_unknown_scope_requests() -> None:
    empty = run_lint("--language", "python", "--paths")
    unknown = run_lint("--scope", "not-a-scope")

    assert empty.returncode == 2
    assert "--paths requires --language and at least one path" in empty.stdout
    assert unknown.returncode == 2
    assert "Unknown maintained lint scope: not-a-scope" in unknown.stdout


@pytest.mark.parametrize(
    ("language", "filename", "source", "expected"),
    [
        ("python", "invalid.py", "def broken():\n    return missing_name\n", "F821"),
        ("javascript", "invalid.js", "export const broken = missingName;\n", "no-undef"),
    ],
)
def test_runner_fails_on_genuine_source_defects(
    language: str,
    filename: str,
    source: str,
    expected: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix=".repository-lint-contract-", dir=REPO_ROOT / "tests") as temp:
        path = Path(temp) / filename
        path.write_text(source, encoding="utf-8")
        relative = path.relative_to(REPO_ROOT).as_posix()

        result = run_lint("--language", language, "--paths", relative)

    assert result.returncode == 1
    assert expected in result.stdout

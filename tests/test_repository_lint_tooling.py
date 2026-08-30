"""Contract tests for repository-owned lint target resolution."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "tooling" / "lint" / "run_lint.py"


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
    assert config["scopes"]["docs-viewer"]["python"] == [
        "docs-viewer/build",
        "docs-viewer/services",
    ]
    assert config["scopes"]["docs-viewer"]["javascript"] == [
        "docs-viewer/runtime/js"
    ]
    assert "site/docs-viewer/runtime/js/**" in config["exclude"]


def test_workflows_cover_canonical_docs_viewer_projection_sources() -> None:
    source_lint = (REPO_ROOT / ".github/workflows/source-lint.yml").read_text(
        encoding="utf-8"
    )
    public_site = (REPO_ROOT / ".github/workflows/public-site.yml").read_text(
        encoding="utf-8"
    )

    assert '"docs-viewer/runtime/js/**"' in source_lint
    for stylesheet in (
        "docs-viewer/static/css/docs-viewer-reports.css",
        "docs-viewer/static/css/docs-viewer-theme.css",
        "docs-viewer/static/css/docs-viewer.css",
    ):
        assert f'"{stylesheet}"' in source_lint
        assert f'"{stylesheet}"' in public_site
    for path in (
        "docs-viewer/runtime/js/public/**",
        "docs-viewer/runtime/js/shared/**",
        "docs-viewer/runtime/js/reports/docs-viewer-public-reports.js",
    ):
        assert f'"{path}"' in public_site
    assert "run: python site-tools/site_validate.py" in public_site
    assert not [
        line
        for line in public_site.splitlines()
        if line.strip().startswith("run:") and "site-code-update" in line
    ]


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
    with pytest.raises(runner.LintTargetError, match="No eligible javascript source"):
        runner.candidate_files(
            ["site/docs-viewer/runtime/js"],
            language="javascript",
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

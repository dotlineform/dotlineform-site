#!/usr/bin/env python3
"""Run optional repo check profiles and write local run logs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "var" / "test-runs"
JEKYLL_DESTINATION = Path("/tmp/dlf-jekyll-build")


@dataclass(frozen=True)
class CheckCommand:
    name: str
    argv: tuple[str, ...]
    description: str


def bundle_argv() -> tuple[str, ...]:
    local_bundle = Path.home() / ".rbenv" / "shims" / "bundle"
    bundle = str(local_bundle) if local_bundle.exists() else "bundle"
    return (bundle, "exec", "jekyll", "build", "--quiet", "--destination", str(JEKYLL_DESTINATION))


PROFILE_COMMANDS: dict[str, tuple[CheckCommand, ...]] = {
    "quick": (
        CheckCommand("git-diff-check", ("git", "diff", "--check"), "Check staged and unstaged diff whitespace."),
        CheckCommand(
            "python-syntax",
            (
                sys.executable,
                "-m",
                "py_compile",
                "scripts/run_checks.py",
                "scripts/studio_backup_retention.py",
                "scripts/audit_studio_ready_state.py",
                "scripts/verify_activity_contract.py",
                "scripts/studio/audit_service.py",
                "tests/python/test_activity_contract.py",
                "tests/python/test_catalogue_activity_context.py",
                "tests/python/test_catalogue_field_registry.py",
                "tests/python/test_studio_backup_retention.py",
            ),
            "Compile lightweight Python check scripts.",
        ),
        CheckCommand(
            "activity-contract-tests",
            (sys.executable, "tests/python/test_activity_contract.py"),
            "Verify Studio activity contract registry shape and v1 save-work coverage.",
        ),
        CheckCommand(
            "catalogue-activity-context-tests",
            (sys.executable, "tests/python/test_catalogue_activity_context.py"),
            "Verify Studio save-work activity context normalization.",
        ),
        CheckCommand(
            "studio-backup-retention-tests",
            (sys.executable, "tests/python/test_studio_backup_retention.py"),
            "Verify local Studio backup retention planning.",
        ),
        CheckCommand(
            "studio-ready-state-audit",
            (sys.executable, "scripts/audit_studio_ready_state.py", "--strict"),
            "Audit Studio route-ready template contracts.",
        ),
        CheckCommand(
            "studio-config-json",
            (sys.executable, "-m", "json.tool", "assets/studio/data/studio_config.json"),
            "Parse Studio config JSON.",
        ),
        CheckCommand(
            "activity-contract-json",
            (sys.executable, "-m", "json.tool", "assets/studio/data/activity_contract.json"),
            "Parse Studio activity contract JSON.",
        ),
    ),
    "catalogue": (
        CheckCommand(
            "catalogue-field-registry",
            (sys.executable, "tests/python/test_catalogue_field_registry.py"),
            "Verify representative catalogue field-registry build plans.",
        ),
        CheckCommand(
            "catalogue-media-cleanup",
            (sys.executable, "tests/python/test_catalogue_media_cleanup.py"),
            "Verify staged catalogue thumbnails are removed after asset copy.",
        ),
        CheckCommand(
            "catalogue-build-preview-downloads",
            ("./scripts/catalogue_json_build.py", "--work-id", "00001", "--changed-fields", "downloads"),
            "Preview a narrow field-aware catalogue build plan.",
        ),
    ),
    "docs": (
        CheckCommand(
            "docs-export-tests",
            (sys.executable, "tests/python/test_docs_export.py"),
            "Verify Docs Viewer export configs and representative Library export dry-runs.",
        ),
        CheckCommand(
            "export-import-adapter-tests",
            (sys.executable, "tests/python/test_export_import_adapters.py"),
            "Verify export/import adapter dispatch and future stub rejection.",
        ),
        CheckCommand(
            "docs-import-tests",
            (sys.executable, "tests/python/test_docs_import.py"),
            "Verify staged Library import parsing and preview rendering.",
        ),
        CheckCommand(
            "docs-import-service-tests",
            (sys.executable, "tests/python/test_docs_import_service.py"),
            "Verify Docs Management Library import service handlers.",
        ),
        CheckCommand(
            "docs-management-server-tests",
            (sys.executable, "tests/python/test_docs_management_server.py"),
            "Verify Docs Management Server archive-parent handling.",
        ),
        CheckCommand(
            "docs-broken-links-tests",
            (sys.executable, "tests/python/test_docs_broken_links.py"),
            "Verify Docs Broken Links audit filtering.",
        ),
        CheckCommand(
            "studio-docs-build",
            ("./scripts/build_docs.rb", "--scope", "studio", "--write"),
            "Regenerate Studio docs-viewer payloads.",
        ),
        CheckCommand(
            "studio-search-build",
            ("./scripts/build_search.rb", "--scope", "studio", "--write"),
            "Regenerate Studio docs search payload.",
        ),
    ),
    "studio-smoke": (
        CheckCommand(
            "jekyll-temp-build",
            bundle_argv(),
            "Build the site to a temporary destination for browser smoke tests.",
        ),
        CheckCommand(
            "data-import-smoke",
            (
                sys.executable,
                "tests/smoke/data_import.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--block-docs-service",
            ),
            "Smoke-check the Studio data import route ready state with docs-management unavailable.",
        ),
        CheckCommand(
            "data-import-unsupported-adapter-smoke",
            (
                sys.executable,
                "tests/smoke/data_import.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--block-docs-service",
                "--route-path",
                "/studio/import/?scope=catalogue",
                "--expect-unsupported",
                "Catalogue import staging is not implemented yet.",
            ),
            "Smoke-check that future import adapter stubs render disabled unavailable states.",
        ),
        CheckCommand(
            "data-import-preview-smoke",
            (
                sys.executable,
                "tests/smoke/data_import.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--mock-docs-service",
            ),
            "Smoke-check the Studio data import preview list flow with a mocked docs-management service.",
        ),
    ),
}

FULL_PROFILE_ORDER = ("quick", "catalogue", "docs", "studio-smoke")


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip().lower())
    return value.strip("-") or "check"


def command_text(argv: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in argv)


def create_run_dir(run_id: str | None) -> Path:
    if run_id:
        safe_id = slugify(run_id)
    else:
        safe_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / safe_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def expand_profiles(profile_names: Iterable[str]) -> list[CheckCommand]:
    commands: list[CheckCommand] = []
    seen: set[str] = set()
    for profile in profile_names:
        profile_commands = []
        if profile == "full":
            for child in FULL_PROFILE_ORDER:
                profile_commands.extend(PROFILE_COMMANDS[child])
        else:
            profile_commands.extend(PROFILE_COMMANDS[profile])
        for command in profile_commands:
            if command.name in seen:
                continue
            seen.add(command.name)
            commands.append(command)
    return commands


def run_command(command: CheckCommand, log_path: Path) -> dict[str, object]:
    started = time.monotonic()
    started_at = dt.datetime.now(dt.timezone.utc).isoformat()
    header = [
        f"name: {command.name}",
        f"description: {command.description}",
        f"cwd: {REPO_ROOT}",
        f"command: {command_text(command.argv)}",
        f"started_at_utc: {started_at}",
        "",
    ]

    try:
        result = subprocess.run(
            command.argv,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = result.stdout or ""
        exit_code = result.returncode
    except FileNotFoundError as error:
        output = f"{error}\n"
        exit_code = 127

    duration = time.monotonic() - started
    footer = [
        "",
        f"exit_code: {exit_code}",
        f"duration_seconds: {duration:.2f}",
    ]
    log_path.write_text("\n".join(header) + output + "\n".join(footer) + "\n", encoding="utf-8")

    return {
        "name": command.name,
        "description": command.description,
        "command": list(command.argv),
        "exit_code": exit_code,
        "duration_seconds": round(duration, 2),
        "log": str(log_path.relative_to(REPO_ROOT)),
    }


def write_summaries(run_dir: Path, profiles: list[str], results: list[dict[str, object]]) -> None:
    failed = [result for result in results if result["exit_code"] != 0]
    summary = {
        "profiles": profiles,
        "status": "failed" if failed else "passed",
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Check Run Summary",
        "",
        f"- Status: {summary['status']}",
        f"- Profiles: {', '.join(profiles)}",
        f"- Run directory: `{summary['run_dir']}`",
        "",
        "## Results",
        "",
    ]
    for result in results:
        status = "pass" if result["exit_code"] == 0 else "fail"
        lines.append(f"- {status}: `{result['name']}` ({result['duration_seconds']}s) - `{result['log']}`")
    lines.append("")
    (run_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        action="append",
        choices=sorted([*PROFILE_COMMANDS.keys(), "full"]),
        default=[],
        help="Check profile to run. Repeat to combine profiles. Defaults to quick.",
    )
    parser.add_argument("--run-id", help="Optional local run id for var/test-runs/.")
    parser.add_argument("--list", action="store_true", help="List available profiles and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list:
        for name in sorted([*PROFILE_COMMANDS.keys(), "full"]):
            if name == "full":
                descriptions = ", ".join(FULL_PROFILE_ORDER)
            else:
                descriptions = ", ".join(command.name for command in PROFILE_COMMANDS[name])
            print(f"{name}: {descriptions}")
        return 0

    profiles = args.profile or ["quick"]
    commands = expand_profiles(profiles)
    run_dir = create_run_dir(args.run_id)

    results: list[dict[str, object]] = []
    total = len(commands)
    for index, command in enumerate(commands, start=1):
        log_path = run_dir / f"{index:03d}-{slugify(command.name)}.log"
        print(f"[{index}/{total}] {command.name}")
        result = run_command(command, log_path)
        results.append(result)
        status = "pass" if result["exit_code"] == 0 else "fail"
        print(f"  {status}: {result['log']}")

    write_summaries(run_dir, profiles, results)
    failed = [result for result in results if result["exit_code"] != 0]
    print(f"summary: {run_dir.relative_to(REPO_ROOT) / 'summary.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

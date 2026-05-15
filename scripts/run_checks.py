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


def pytest_argv(*paths: str) -> tuple[str, ...]:
    return (sys.executable, "-m", "pytest", "-q", *paths)


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
                "scripts/local_env.py",
                "scripts/pipeline_config.py",
                "scripts/checks/audit_site_consistency.py",
                "scripts/checks/css_token_audit.py",
                "scripts/media/publish_media_to_r2.py",
                "scripts/media/build_palette_data.py",
                "scripts/catalogue/catalogue_json_build.py",
                "scripts/catalogue/catalogue_build_commands.py",
                "scripts/catalogue/catalogue_build_field_plan.py",
                "scripts/catalogue/catalogue_build_media.py",
                "scripts/catalogue/catalogue_build_scopes.py",
                "scripts/catalogue/generate_work_pages.py",
                "scripts/catalogue/catalogue_generation_common.py",
                "scripts/catalogue/catalogue_generation_indexes.py",
                "scripts/catalogue/catalogue_generation_moments.py",
                "scripts/catalogue/catalogue_generation_recent.py",
                "scripts/catalogue/catalogue_generation_records.py",
                "scripts/catalogue/catalogue_generation_source_updates.py",
                "scripts/catalogue/catalogue_generation_writes.py",
                "scripts/media/make_srcset_images.py",
                "scripts/catalogue/project_state_report.py",
                "scripts/catalogue/catalogue_write_server.py",
                "scripts/studio/studio_backup_retention.py",
                "scripts/checks/audit_studio_ready_state.py",
                "scripts/checks/verify_activity_contract.py",
                "scripts/studio_activity.py",
                "scripts/docs/docs_activity.py",
                "scripts/analytics/tag_activity.py",
                "scripts/analytics/tag_alias_mutations.py",
                "scripts/analytics/tag_assignment_service.py",
                "scripts/analytics/tag_promotion_mutations.py",
                "scripts/analytics/tag_registry_mutations.py",
                "scripts/analytics/tag_source_model.py",
                "scripts/analytics/tag_write_transactions.py",
                "scripts/docs/docs_import_source_service.py",
                "scripts/docs/docs_live_rebuild_watcher.py",
                "scripts/docs/docs_management_server.py",
                "scripts/docs/docs_management_mutations.py",
                "scripts/docs/docs_scope_manifest.py",
                "scripts/analytics/tag_routes.py",
                "scripts/catalogue/catalogue_source.py",
                "scripts/catalogue/catalogue_cleanup.py",
                "scripts/catalogue/catalogue_delete_plans.py",
                "scripts/catalogue/catalogue_invalidation.py",
                "scripts/catalogue/catalogue_lookup_refresh.py",
                "scripts/catalogue/catalogue_publication.py",
                "scripts/catalogue/catalogue_prose_import.py",
                "scripts/catalogue/catalogue_routes.py",
                "scripts/catalogue/catalogue_save_build.py",
                "scripts/catalogue/catalogue_source_mutation.py",
                "scripts/catalogue/catalogue_transactions.py",
                "scripts/studio/audit_service.py",
                "tests/smoke/docs_viewer_routes.py",
                "tests/smoke/docs_viewer_management_modal.py",
                "tests/smoke/ui_catalogue_modal_demo.py",
                "tests/python/test_activity_contract.py",
                "tests/python/test_local_env.py",
                "tests/python/test_publish_media_to_r2.py",
                "tests/python/test_docs_activity.py",
                "tests/python/test_tag_activity.py",
                "tests/python/test_tag_alias_mutations.py",
                "tests/python/test_tag_assignment_service.py",
                "tests/python/test_tag_promotion_mutations.py",
                "tests/python/test_tag_registry_mutations.py",
                "tests/python/test_tag_source_model.py",
                "tests/python/test_tag_write_transactions.py",
                "tests/python/test_docs_live_rebuild_watcher.py",
                "tests/python/test_docs_management_mutations.py",
                "tests/python/test_tag_routes.py",
                "tests/python/test_catalogue_cleanup.py",
                "tests/python/test_catalogue_delete_plans.py",
                "tests/python/test_catalogue_invalidation.py",
                "tests/python/test_catalogue_lookup_refresh.py",
                "tests/python/test_catalogue_publication.py",
                "tests/python/test_catalogue_prose_import.py",
                "tests/python/test_catalogue_routes.py",
                "tests/python/test_catalogue_save_build.py",
                "tests/python/test_catalogue_source_mutation.py",
                "tests/python/test_catalogue_transactions.py",
                "tests/python/test_studio_activity_context.py",
                "tests/python/test_studio_activity_feed.py",
                "tests/python/test_catalogue_field_registry.py",
                "tests/python/test_catalogue_build_commands.py",
                "tests/python/test_catalogue_build_field_plan.py",
                "tests/python/test_catalogue_build_media.py",
                "tests/python/test_catalogue_build_scopes.py",
                "tests/python/test_catalogue_generation_indexes.py",
                "tests/python/test_catalogue_generation_moments.py",
                "tests/python/test_catalogue_generation_recent.py",
                "tests/python/test_catalogue_generation_records.py",
                "tests/python/test_catalogue_generation_source_updates.py",
                "tests/python/test_catalogue_generation_writes.py",
                "tests/python/test_studio_backup_retention.py",
            ),
            "Compile lightweight Python check scripts.",
        ),
        CheckCommand(
            "quick-python-pytest",
            pytest_argv(
                "tests/python/test_activity_contract.py",
                "tests/python/test_local_env.py",
                "tests/python/test_publish_media_to_r2.py",
                "tests/python/test_catalogue_invalidation.py",
                "tests/python/test_catalogue_lookup_refresh.py",
                "tests/python/test_catalogue_cleanup.py",
                "tests/python/test_catalogue_delete_plans.py",
                "tests/python/test_catalogue_publication.py",
                "tests/python/test_catalogue_prose_import.py",
                "tests/python/test_catalogue_transactions.py",
                "tests/python/test_catalogue_routes.py",
                "tests/python/test_tag_routes.py",
                "tests/python/test_tag_activity.py",
                "tests/python/test_tag_alias_mutations.py",
                "tests/python/test_tag_assignment_service.py",
                "tests/python/test_tag_promotion_mutations.py",
                "tests/python/test_tag_registry_mutations.py",
                "tests/python/test_tag_source_model.py",
                "tests/python/test_tag_write_transactions.py",
                "tests/python/test_catalogue_save_build.py",
                "tests/python/test_catalogue_source_mutation.py",
                "tests/python/test_studio_activity_context.py",
                "tests/python/test_studio_activity_feed.py",
                "tests/python/test_studio_backup_retention.py",
                "tests/python/test_catalogue_build_commands.py",
                "tests/python/test_catalogue_build_scopes.py",
                "tests/python/test_catalogue_build_field_plan.py",
                "tests/python/test_catalogue_build_media.py",
                "tests/python/test_catalogue_generation_moments.py",
                "tests/python/test_catalogue_generation_recent.py",
                "tests/python/test_catalogue_generation_writes.py",
                "tests/python/test_catalogue_generation_source_updates.py",
            ),
            "Run quick-profile Python tests through pytest collection.",
        ),
        CheckCommand(
            "studio-ready-state-audit",
            (sys.executable, "scripts/checks/audit_studio_ready_state.py", "--strict"),
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
            "catalogue-python-pytest",
            pytest_argv(
                "tests/python/test_catalogue_field_registry.py",
                "tests/python/test_catalogue_media_cleanup.py",
            ),
            "Run catalogue-profile Python tests through pytest collection.",
        ),
        CheckCommand(
            "catalogue-build-preview-downloads",
            ("./scripts/catalogue/catalogue_json_build.py", "--work-id", "00001", "--changed-fields", "downloads"),
            "Preview a narrow field-aware catalogue build plan.",
        ),
    ),
    "docs": (
        CheckCommand(
            "docs-python-pytest",
            pytest_argv(
                "tests/python/test_docs_export.py",
                "tests/python/test_data_sharing_adapters.py",
                "tests/python/test_data_sharing_service.py",
                "tests/python/test_docs_import.py",
                "tests/python/test_docs_import_service.py",
                "tests/python/test_docs_generated_reads.py",
                "tests/python/test_docs_activity.py",
                "tests/python/test_docs_live_rebuild_watcher.py",
                "tests/python/test_docs_write_rebuild.py",
                "tests/python/test_docs_management_mutations.py",
                "tests/python/test_docs_management_server.py",
                "tests/python/test_docs_management_routes.py",
                "tests/python/test_docs_broken_links.py",
            ),
            "Run docs-profile Python tests through pytest collection.",
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
    "docs-viewer-smoke": (
        CheckCommand(
            "jekyll-temp-build",
            bundle_argv(),
            "Build the site to a temporary destination for browser smoke tests.",
        ),
        CheckCommand(
            "docs-viewer-route-smoke",
            (
                sys.executable,
                "tests/smoke/docs_viewer_routes.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check Docs Viewer direct route, search, link interception, history, hash, and Library scope behavior.",
        ),
        CheckCommand(
            "docs-viewer-management-modal-smoke",
            (
                sys.executable,
                "tests/smoke/docs_viewer_management_modal.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check Docs Viewer management modal semantics, action rows, focus behavior, and mobile sizing.",
        ),
    ),
    "studio-smoke": (
        CheckCommand(
            "jekyll-temp-build",
            bundle_argv(),
            "Build the site to a temporary destination for browser smoke tests.",
        ),
        CheckCommand(
            "docs-viewer-route-smoke",
            (
                sys.executable,
                "tests/smoke/docs_viewer_routes.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check Docs Viewer direct route, search, link interception, history, hash, and Library scope behavior.",
        ),
        CheckCommand(
            "ui-catalogue-modal-demo-smoke",
            (
                sys.executable,
                "tests/smoke/ui_catalogue_modal_demo.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check the UI Catalogue modal shell demo semantics, focus behavior, validation, and mobile sizing.",
        ),
        CheckCommand(
            "data-sharing-prepare-smoke",
            (
                sys.executable,
                "tests/smoke/data_sharing_prepare.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--block-docs-service",
            ),
            "Smoke-check the Studio data sharing prepare route ready state with docs-management unavailable.",
        ),
        CheckCommand(
            "activity-log-modal-smoke",
            (
                sys.executable,
                "tests/smoke/activity_log_modal.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check the Studio activity detail notice modal shell behavior.",
        ),
        CheckCommand(
            "data-sharing-review-smoke",
            (
                sys.executable,
                "tests/smoke/data_sharing_review.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--block-docs-service",
            ),
            "Smoke-check the Studio data sharing review route ready state with docs-management unavailable.",
        ),
        CheckCommand(
            "data-sharing-review-tags-unavailable-smoke",
            (
                sys.executable,
                "tests/smoke/data_sharing_review.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--block-docs-service",
                "--route-path",
                "/studio/data-sharing/review/?scope=tags",
            ),
            "Smoke-check the Tags returned package review route with docs-management unavailable.",
        ),
        CheckCommand(
            "data-sharing-review-preview-smoke",
            (
                sys.executable,
                "tests/smoke/data_sharing_review.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
                "--mock-docs-service",
            ),
            "Smoke-check the Studio returned package review list flow with a mocked docs-management service.",
        ),
        CheckCommand(
            "catalogue-series-modal-smoke",
            (
                sys.executable,
                "tests/smoke/catalogue_series_modal.py",
                "--site-root",
                str(JEKYLL_DESTINATION),
            ),
            "Smoke-check the Catalogue Series confirmation modal shell behavior.",
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

#!/usr/bin/env python3
"""Scoped JSON-source catalogue build helper."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "_config.yml").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)
SCRIPTS_DIR = REPO_ROOT / "scripts"

from catalogue import catalogue_build_commands as build_commands
from catalogue import catalogue_build_field_plan as build_field_plan
from catalogue import catalogue_build_media as build_media
from catalogue import catalogue_build_scopes as build_scopes
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR
from local_env import runtime_env


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def run_scoped_build_scope(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    write: bool,
    force: bool = False,
    media_only: bool = False,
) -> Dict[str, Any]:
    env = runtime_env()
    scope_kind = str(scope.get("kind") or "work").strip().lower()
    refresh_published = True
    effective_force = bool(force)
    generate_local_media = bool(scope.get("generate_local_media", True))
    rebuild_search = bool(scope.get("rebuild_search", True))
    generate_only = list(scope.get("generate_only") or [])
    run_generate = bool(generate_only)
    if generate_local_media:
        media_step = build_media.execute_local_media_plan(repo_root, scope=scope, write=write, env=env, force=force)
    else:
        media_step = {
            "label": "Generate Local Media Derivatives",
            "status": "skipped",
            "summary": "Local media not selected by this field-aware scope.",
            "generated": {"work": [], "work_details": [], "moment": []},
            "planned": {"work": [], "work_details": [], "moment": []},
            "current": {"work": [], "work_details": [], "moment": []},
            "blocked": {"work": [], "work_details": [], "moment": []},
            "exit_code": 0,
        }
    commands: list[tuple[str, list[str]]] = []
    if scope_kind == "moment":
        if run_generate:
            commands.append(
                (
                    "Generate Moment Pages",
                    build_commands.build_generate_moment_command(
                        repo_root,
                        repo_root / DEFAULT_SOURCE_DIR,
                        scope,
                        write=write,
                        force=effective_force,
                        refresh_published=refresh_published,
                    ),
                )
            )
    else:
        if run_generate:
            commands.append(
                (
                    "Generate Work Pages",
                    build_commands.build_generate_command(
                        repo_root,
                        Path(scope["source_dir"]),
                        scope,
                        write=write,
                        force=effective_force,
                        refresh_published=refresh_published,
                    ),
                )
            )
    if rebuild_search:
        commands.append(
            (
                "Build Catalogue Search Index",
                build_commands.build_search_command(repo_root, write=write, force=effective_force, env=env),
            )
        )
    steps: list[Dict[str, Any]] = []
    status = "completed"
    failed_step = ""
    failure_message = ""

    steps.append(
        {
            "label": media_step.get("label", "Generate Local Media Derivatives"),
            "command": [],
            "exit_code": int(media_step.get("exit_code", 0)),
            "stdout_tail": str(media_step.get("stdout_tail") or media_step.get("summary") or "").strip(),
            "stderr_tail": str(media_step.get("stderr_tail") or "").strip(),
            "status": str(media_step.get("status") or "completed"),
        }
    )
    if media_step.get("status") == "failed":
        status = "failed"
        failed_step = str(media_step.get("label") or "Generate Local Media Derivatives")
        failure_message = str(media_step.get("stderr_tail") or media_step.get("summary") or "Local media generation failed.")

    if status != "failed" and not media_only:
        for label, cmd in commands:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_root),
                env=env,
                text=True,
                capture_output=True,
            )
            step = build_commands.normalize_subprocess_step(
                label,
                cmd,
                returncode=proc.returncode,
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
            )
            steps.append(step)
            if int(step.get("exit_code", 0)) != 0:
                status = "failed"
                failed_step = label
                failure_message = build_commands.step_failure_message(label, step)
                break

    response: Dict[str, Any] = {
        "scope": scope,
        "status": status,
        "write": bool(write),
        "force": effective_force,
        "media_only": bool(media_only),
        "refresh_published": refresh_published,
        "steps": steps,
        "media": {
            "generated": media_step.get("generated", {"work": [], "work_details": [], "moment": []}),
            "current": media_step.get("current", {"work": [], "work_details": [], "moment": []}),
            "blocked": media_step.get("blocked", {"work": [], "work_details": [], "moment": []}),
            "status": media_step.get("status", "completed"),
            "summary": media_step.get("summary", ""),
        },
    }
    if failed_step:
        response["failed_step"] = failed_step
        response["error"] = failure_message

    return response


def print_preview(scope: Dict[str, Any], repo_root: Path, source_dir: Path, *, force: bool, media_only: bool) -> None:
    if media_only:
        if scope.get("kind") == "moment":
            ids = ", ".join(scope.get("moment_ids", [])) or "none"
            print(f"Refresh local media derivatives for moments [{ids}].")
        else:
            ids = ", ".join(scope.get("work_ids", [])) or "none"
            detail_uid = str(scope.get("detail_uid") or "").strip()
            suffix = f", detail {detail_uid}" if detail_uid else ""
            print(f"Refresh local media derivatives for works [{ids}]{suffix}.")
    else:
        print(scope["summary"])
    print(f"Source mode: {scope['source_mode']}")
    if scope.get("kind") == "moment":
        print(f"Moment IDs: {', '.join(scope['moment_ids']) if scope['moment_ids'] else 'none'}")
        print(f"Moment file: {scope.get('moment_file') or 'none'}")
    else:
        print(f"Work IDs: {', '.join(scope['work_ids']) if scope['work_ids'] else 'none'}")
        print(f"Series IDs: {', '.join(scope['series_ids']) if scope['series_ids'] else 'none'}")
    print(f"Published refresh: {'no' if media_only else 'yes'}")
    print(f"Search rebuild: {'no' if media_only else 'yes' if scope['rebuild_search'] else 'no'}")
    print(f"Media only: {'yes' if media_only else 'no'}")
    field_plan = scope.get("field_plan") if isinstance(scope.get("field_plan"), dict) else {}
    if field_plan:
        print(f"Field-aware mode: {field_plan.get('mode') or 'unknown'}")
        print(f"Field-aware rules: {', '.join(field_plan.get('rule_ids') or []) or 'none'}")
        print(f"Field-aware artifacts: {', '.join(field_plan.get('artifacts') or []) or 'none'}")
        explanation_lines = build_field_plan.field_plan_explanation_lines(field_plan)
        if explanation_lines:
            print("Field-aware reasons:")
            for line in explanation_lines:
                print(f"  - {line}")
    media_plan = (
        build_media.build_local_media_plan(repo_root, scope=scope, force=force)
        if bool(scope.get("generate_local_media", True))
        else {"counts": {"pending": 0, "current": 0, "blocked": 0, "unavailable": 0}}
    )
    media_counts = media_plan.get("counts", {})
    print(
        "Local media: "
        f"pending {int(media_counts.get('pending', 0))}, "
        f"current {int(media_counts.get('current', 0))}, "
        f"blocked {int(media_counts.get('blocked', 0))}, "
        f"unavailable {int(media_counts.get('unavailable', 0))}"
    )
    if media_only:
        print("Commands: media-only internal derivative refresh")
        return
    print("Commands:")
    commands: list[list[str]] = []
    if scope.get("generate_only"):
        if scope.get("kind") == "moment":
            commands.append(
                build_commands.build_generate_moment_command(
                    repo_root,
                    repo_root / DEFAULT_SOURCE_DIR,
                    scope,
                    write=False,
                    force=bool(force),
                    refresh_published=True,
                )
            )
        else:
            commands.append(
                build_commands.build_generate_command(
                    repo_root,
                    source_dir,
                    scope,
                    write=False,
                    force=force,
                    refresh_published=True,
                )
            )
    if bool(scope.get("rebuild_search")):
        commands.append(build_commands.build_search_command(repo_root, write=False, force=bool(force), env=runtime_env()))
    if commands:
        for cmd in commands:
            print("  + " + " ".join(cmd))
    else:
        print("  (none)")


def print_thumbnail_only_preview(repo_root: Path, source_dir: Path, *, force: bool) -> None:
    print("Regenerate catalogue thumbnails for all works, work details, and moments.")
    print("Source mode: canonical JSON")
    print("Thumbnail only: yes")
    print("Primary derivatives: no")
    print("Search rebuild: no")
    print("Published refresh: no")
    plan = build_media.build_catalogue_thumbnail_only_plan(
        repo_root,
        source_dir=source_dir,
        env=runtime_env(),
        force=force,
    )
    counts = plan.get("counts", {})
    print(
        "Thumbnails: "
        f"pending {int(counts.get('pending', 0))}, "
        f"current {int(counts.get('current', 0))}, "
        f"skipped {int(counts.get('skipped', 0))}"
    )
    skipped = [task for task in plan.get("tasks", []) if task.get("status") == "skipped"]
    if skipped:
        print("Skipped sources:")
        for task in skipped[:20]:
            kind = str(task.get("kind") or "")
            item_id = str(task.get("id") or "")
            reason = str(task.get("reason") or "source media is not available")
            print(f"  - {kind} {item_id}: {reason}")
        if len(skipped) > 20:
            print(f"  - ... {len(skipped) - 20} more")
    print("Commands: thumbnail-only internal regeneration")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scoped JSON-source catalogue build helper.")
    parser.add_argument("--work-id", default="", help="Target work_id")
    parser.add_argument("--series-id", default="", help="Target series_id")
    parser.add_argument("--moment-file", default="", help="Target moment markdown filename, for example keys.md")
    parser.add_argument("--detail-uid", default="", help="Optional work detail uid to include in a work-scoped media plan")
    parser.add_argument("--extra-series-ids", default="", help="Additional series ids to include")
    parser.add_argument("--extra-work-ids", default="", help="Additional work ids to include for a series scope")
    parser.add_argument("--repo-root", default="", help="Repo root (auto-detected when omitted)")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Canonical JSON source dir")
    parser.add_argument("--write", action="store_true", help="Run generation and search rebuild")
    parser.add_argument("--force", action="store_true", help="Force generation and search rewrites even when content versions match")
    parser.add_argument("--media-only", action="store_true", help="Only stage source media and regenerate local image derivatives")
    parser.add_argument("--thumbnail-only", action="store_true", help="Only regenerate public work, work-detail, and moment thumbnails from catalogue JSON sources")
    parser.add_argument("--changed-fields", action="append", default=[], help="Optional comma-separated source fields for field-aware preview planning")
    parser.add_argument("--record-family", default="", help="Record family for --changed-fields: work, work_detail, series, or moment")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else detect_repo_root()
    source_dir = (repo_root / args.source_dir).resolve()
    work_id = str(args.work_id or "").strip()
    series_id = str(args.series_id or "").strip()
    moment_file = str(args.moment_file or "").strip()
    if args.thumbnail_only:
        if any(value for value in (work_id, series_id, moment_file, str(args.detail_uid or "").strip())):
            raise SystemExit("--thumbnail-only scans all works, work details, and moments; do not pass scoped record ids.")
        if args.changed_fields or args.record_family:
            raise SystemExit("--thumbnail-only does not use field-aware build planning.")
        if args.media_only:
            raise SystemExit("Pass either --thumbnail-only or --media-only, not both.")
        if not args.write:
            print_thumbnail_only_preview(repo_root, source_dir, force=args.force)
            return
        result = build_media.execute_catalogue_thumbnail_only_plan(
            repo_root,
            source_dir=source_dir,
            write=True,
            env=runtime_env(),
            force=args.force,
        )
        if result["status"] != "completed":
            raise SystemExit(str(result.get("stderr_tail") or result.get("summary") or "Thumbnail regeneration failed."))
        print(str(result.get("summary") or "Thumbnail-only regeneration completed."))
        return
    if sum(1 for value in (work_id, series_id, moment_file) if value) != 1:
        raise SystemExit("Pass exactly one of --work-id, --series-id, or --moment-file.")
    if moment_file:
        scope = build_scopes.build_scope_for_moment(repo_root, moment_file, force=args.force)
    elif series_id:
        scope = build_scopes.build_scope_for_series(source_dir, series_id, extra_work_ids=args.extra_work_ids.split(","))
    else:
        scope = build_scopes.build_scope_for_work(source_dir, work_id, extra_series_ids=args.extra_series_ids.split(","), detail_uid=args.detail_uid)
    changed_fields = build_field_plan.parse_csv_tokens(args.changed_fields)
    if changed_fields:
        plan = build_field_plan.build_field_plan_for_scope(
            repo_root,
            source_dir,
            scope,
            changed_fields=changed_fields,
            record_family=args.record_family,
        )
        build_field_plan.apply_field_build_plan_to_scope(scope, plan)
    if not args.write:
        print_preview(scope, repo_root, source_dir, force=args.force, media_only=args.media_only)
        return

    result = run_scoped_build_scope(
        repo_root,
        scope=scope,
        write=True,
        force=args.force,
        media_only=args.media_only,
    )
    if result["status"] != "completed":
        raise SystemExit(str(result.get("error") or "Scoped JSON build failed."))
    if args.media_only:
        print("Media-only derivative refresh completed.")
    else:
        print(scope["summary"])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Scoped JSON-source catalogue build helper."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence

from build_activity import append_build_activity
from catalogue_source import DEFAULT_SOURCE_DIR, normalize_status, records_from_json_source, slug_id
from series_ids import normalize_series_id


DEFAULT_ARTIFACTS = [
    "work-pages",
    "work-json",
    "series-pages",
    "series-index-json",
    "works-index-json",
    "recent-index-json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def normalize_series_ids(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            series_id = normalize_series_id(token)
            if series_id in seen:
                continue
            seen.add(series_id)
            out.append(series_id)
    return out


def validate_buildable_series_scope(records, series_ids: Sequence[str]) -> None:
    work_series_ids_by_work_id: dict[str, list[str]] = {}
    for work_id, work_record in records.works.items():
        raw_series_ids = work_record.get("series_ids", [])
        if isinstance(raw_series_ids, list):
            work_series_ids_by_work_id[work_id] = normalize_series_ids(raw_series_ids)
        else:
            work_series_ids_by_work_id[work_id] = []

    errors: list[str] = []
    for series_id in series_ids:
        series_record = records.series.get(series_id)
        if not isinstance(series_record, dict):
            errors.append(f"series {series_id}: not found in source records")
            continue
        status = normalize_status(series_record.get("status"))
        if status not in {"draft", "published"}:
            continue
        raw_primary_work_id = str(series_record.get("primary_work_id") or "").strip()
        if not raw_primary_work_id:
            errors.append(f"series {series_id}: missing primary_work_id for runtime build")
            continue
        primary_work_id = slug_id(raw_primary_work_id)
        if primary_work_id not in records.works:
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} not found in works")
            continue
        if series_id not in work_series_ids_by_work_id.get(primary_work_id, []):
            errors.append(f"series {series_id}: primary_work_id {primary_work_id!r} is not in that work's series_ids")

    if errors:
        raise ValueError("series build precondition failed: " + "; ".join(errors[:20]))


def build_scope_for_work(source_dir: Path, work_id: str, extra_series_ids: Sequence[Any] | None = None) -> Dict[str, Any]:
    normalized_work_id = slug_id(work_id)
    records = records_from_json_source(source_dir)
    work_record = records.works.get(normalized_work_id)
    if not isinstance(work_record, dict):
        raise ValueError(f"work_id not found: {normalized_work_id}")

    current_series_ids = normalize_series_ids(work_record.get("series_ids", []))
    requested_extra_series_ids = normalize_series_ids(extra_series_ids or [])
    series_ids = normalize_series_ids([*current_series_ids, *requested_extra_series_ids])
    validate_buildable_series_scope(records, series_ids)
    return {
        "work_ids": [normalized_work_id],
        "series_ids": series_ids,
        "current_series_ids": current_series_ids,
        "extra_series_ids": [series_id for series_id in requested_extra_series_ids if series_id not in current_series_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "summary": summarize_scope([normalized_work_id], series_ids),
    }


def build_scope_for_series(source_dir: Path, series_id: str, extra_work_ids: Sequence[Any] | None = None) -> Dict[str, Any]:
    normalized_series_id = normalize_series_id(series_id)
    records = records_from_json_source(source_dir)
    series_record = records.series.get(normalized_series_id)
    if not isinstance(series_record, dict):
        raise ValueError(f"series_id not found: {normalized_series_id}")

    current_work_ids: list[str] = []
    for work_id, work_record in records.works.items():
        series_ids = work_record.get("series_ids", [])
        if isinstance(series_ids, list) and normalized_series_id in normalize_series_ids(series_ids):
            current_work_ids.append(work_id)
    current_work_ids = sorted(current_work_ids)

    requested_extra_work_ids: list[str] = []
    seen_extra: set[str] = set()
    for raw in extra_work_ids or []:
        text = str(raw or "").strip()
        if not text:
            continue
        for part in text.split(","):
            token = str(part or "").strip()
            if not token:
                continue
            work_id = slug_id(token)
            if work_id in seen_extra:
                continue
            seen_extra.add(work_id)
            requested_extra_work_ids.append(work_id)

    work_ids = sorted({*current_work_ids, *requested_extra_work_ids})
    validate_buildable_series_scope(records, [normalized_series_id])
    return {
        "work_ids": work_ids,
        "series_ids": [normalized_series_id],
        "current_work_ids": current_work_ids,
        "extra_work_ids": [work_id for work_id in requested_extra_work_ids if work_id not in current_work_ids],
        "generate_only": list(DEFAULT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "json",
        "source_dir": str(source_dir),
        "summary": summarize_scope(work_ids, [normalized_series_id]),
    }


def summarize_scope(work_ids: Sequence[str], series_ids: Sequence[str]) -> str:
    work_text = ", ".join(work_ids) if work_ids else "none"
    series_text = ", ".join(series_ids) if series_ids else "none"
    return f"Build works [{work_text}], series [{series_text}], aggregate indexes, and catalogue search."


def resolve_bundle_bin(env: Dict[str, str] | None = None) -> str:
    env = env or os.environ
    home = Path(env.get("HOME", "")).expanduser()
    shim = home / ".rbenv/shims/bundle"
    if shim.exists() and os.access(shim, os.X_OK):
        return str(shim)
    return env.get("BUNDLE_BIN", "bundle")


def build_generate_command(repo_root: Path, source_dir: Path, scope: Dict[str, Any], *, write: bool, force: bool) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_work_pages.py"),
        "--source",
        "json",
        "--source-dir",
        str(source_dir),
        "--work-ids",
        ",".join(scope["work_ids"]),
    ]
    series_ids = list(scope.get("series_ids", []))
    if series_ids:
        cmd += ["--series-ids", ",".join(series_ids)]
    for artifact in scope.get("generate_only", []):
        cmd += ["--only", str(artifact)]
    if write:
        cmd.append("--write")
    if force:
        cmd.append("--force")
    return cmd


def build_search_command(repo_root: Path, *, write: bool, force: bool, env: Dict[str, str] | None = None) -> list[str]:
    bundle_bin = resolve_bundle_bin(env)
    cmd = [
        bundle_bin,
        "exec",
        "ruby",
        str(repo_root / "scripts" / "build_search.rb"),
        "--scope",
        "catalogue",
    ]
    if write:
        cmd.append("--write")
    if force:
        cmd.append("--force")
    return cmd


def run_scoped_build_scope(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    env = os.environ.copy()
    commands = [
        ("Generate Work Pages", build_generate_command(repo_root, Path(scope["source_dir"]), scope, write=write, force=force)),
        ("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=force, env=env)),
    ]
    steps: list[Dict[str, Any]] = []
    status = "completed"
    failed_step = ""
    failure_message = ""

    for label, cmd in commands:
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            text=True,
            capture_output=True,
        )
        steps.append(
            {
                "label": label,
                "command": cmd,
                "exit_code": proc.returncode,
                "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-8:]) if proc.stdout else "",
                "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-8:]) if proc.stderr else "",
            }
        )
        if proc.returncode != 0:
            status = "failed"
            failed_step = label
            failure_message = proc.stderr.strip() or proc.stdout.strip() or f"{label} failed with exit code {proc.returncode}"
            break

    response: Dict[str, Any] = {
        "scope": scope,
        "status": status,
        "write": bool(write),
        "force": bool(force),
        "steps": steps,
    }
    if failed_step:
        response["failed_step"] = failed_step
        response["error"] = failure_message

    if write and log_activity:
        append_build_activity(
            repo_root,
            build_activity_entry_for_scoped_json_build(
                time_utc=utc_now(),
                status=status,
                work_ids=scope["work_ids"],
                series_ids=scope["series_ids"],
                failed_step=failed_step,
                force=force,
            ),
        )
    return response


def run_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    scope = build_scope_for_work(source_dir, work_id, extra_series_ids=extra_series_ids)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, log_activity=log_activity)


def run_series_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    write: bool,
    force: bool = False,
    log_activity: bool = True,
) -> Dict[str, Any]:
    scope = build_scope_for_series(source_dir, series_id, extra_work_ids=extra_work_ids)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, log_activity=log_activity)


def build_activity_entry_for_scoped_json_build(
    *,
    time_utc: str,
    status: str,
    work_ids: Sequence[str],
    series_ids: Sequence[str],
    failed_step: str = "",
    force: bool = False,
) -> Dict[str, Any]:
    work_ids_list = list(work_ids)
    series_ids_list = list(series_ids)
    summary = (
        f"Scoped JSON build updated {len(work_ids_list)} work records, {len(series_ids_list)} series, and catalogue search."
        if status == "completed"
        else f"Scoped JSON build failed for {len(work_ids_list)} work records."
    )
    return {
        "id": f"{time_utc}-build_catalogue_json-{work_ids_list[0] if work_ids_list else 'none'}",
        "time_utc": time_utc,
        "script": "build_catalogue_json",
        "status": status,
        "dry_run": False,
        "planner_mode": "json-source-scoped",
        "summary": summary,
        "changes": {
            "source": {
                "works": sorted(work_ids_list),
                "series": sorted(series_ids_list),
                "work_details": [],
            },
            "workbook": {
                "works": [],
                "series": [],
                "work_details": [],
                "moments": [],
            },
            "media": {
                "work": [],
                "work_details": [],
                "moment": [],
            },
        },
        "actions": {
            "generate_work_ids": len(work_ids_list),
            "generate_series_ids": len(series_ids_list),
            "rebuild_search": True,
            "force_generate": bool(force),
        },
        "results": {
            "source_mode": "json",
            "work_ids": sorted(work_ids_list),
            "failed_step": failed_step,
        },
    }


def print_preview(scope: Dict[str, Any], repo_root: Path, source_dir: Path, *, force: bool) -> None:
    print(scope["summary"])
    print(f"Source mode: {scope['source_mode']}")
    print(f"Work IDs: {', '.join(scope['work_ids']) if scope['work_ids'] else 'none'}")
    print(f"Series IDs: {', '.join(scope['series_ids']) if scope['series_ids'] else 'none'}")
    print(f"Search rebuild: {'yes' if scope['rebuild_search'] else 'no'}")
    print("Commands:")
    for cmd in [
        build_generate_command(repo_root, source_dir, scope, write=False, force=force),
        build_search_command(repo_root, write=False, force=force),
    ]:
        print("  + " + " ".join(cmd))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scoped JSON-source catalogue build helper.")
    parser.add_argument("--work-id", required=True, help="Target work_id")
    parser.add_argument("--extra-series-ids", default="", help="Additional series ids to include")
    parser.add_argument("--repo-root", default="", help="Repo root (auto-detected when omitted)")
    parser.add_argument("--source-dir", default=str(DEFAULT_SOURCE_DIR), help="Canonical JSON source dir")
    parser.add_argument("--write", action="store_true", help="Run generation and search rebuild")
    parser.add_argument("--force", action="store_true", help="Pass --force to generation and search rebuild")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else detect_repo_root()
    source_dir = (repo_root / args.source_dir).resolve()
    scope = build_scope_for_work(source_dir, args.work_id, extra_series_ids=args.extra_series_ids.split(","))
    if not args.write:
        print_preview(scope, repo_root, source_dir, force=args.force)
        return

    result = run_scoped_build(
        repo_root,
        source_dir=source_dir,
        work_id=args.work_id,
        extra_series_ids=args.extra_series_ids.split(","),
        write=True,
        force=args.force,
        log_activity=True,
    )
    if result["status"] != "completed":
        raise SystemExit(str(result.get("error") or "Scoped JSON build failed."))
    print(scope["summary"])


if __name__ == "__main__":
    main()

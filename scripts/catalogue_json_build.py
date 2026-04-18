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
from moment_sources import build_moment_source_entry, normalize_moment_filename, validate_moment_source_entry
from pipeline_config import env_var_name, env_var_value, load_pipeline_config, source_moments_images_subdir, source_moments_root_subdir
from series_ids import normalize_series_id


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")

DEFAULT_ARTIFACTS = [
    "work-pages",
    "work-json",
    "series-pages",
    "series-index-json",
    "works-index-json",
    "recent-index-json",
]
DEFAULT_MOMENT_ARTIFACTS = ["moments"]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def detect_projects_base_dir(env: Dict[str, str] | None = None) -> Path:
    env = env or os.environ
    value = env_var_value(PIPELINE_CONFIG, "projects_base_dir", env)
    if not value:
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} is required for moment source builds.")
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"{PROJECTS_BASE_DIR_ENV_NAME} does not exist: {path}")
    return path


def build_moment_paths(projects_base_dir: Path, moment_file: str) -> Dict[str, Path]:
    filename = normalize_moment_filename(moment_file)
    moments_root = projects_base_dir / source_moments_root_subdir(PIPELINE_CONFIG)
    moments_images_root = projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG)
    source_path = moments_root / filename
    return {
        "moments_root": moments_root,
        "moments_images_root": moments_images_root,
        "source_path": source_path,
    }


def preview_moment_source(repo_root: Path, moment_file: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    projects_base_dir = detect_projects_base_dir(env)
    paths = build_moment_paths(projects_base_dir, moment_file)
    source_path = paths["source_path"]
    moment_id = source_path.stem.strip().lower()
    preview: Dict[str, Any] = {
        "kind": "moment",
        "moment_id": moment_id,
        "moment_file": source_path.name,
        "source_path": str(Path("moments") / source_path.name),
        "public_url": f"/moments/{moment_id}/",
        "generated_page_path": str(Path("_moments") / f"{moment_id}.md"),
        "generated_json_path": str(Path("assets/moments/index") / f"{moment_id}.json"),
        "moments_index_path": "assets/data/moments_index.json",
        "search_scope": "catalogue",
        "source_exists": source_path.exists(),
        "errors": [],
        "valid": False,
    }

    if not source_path.exists():
        preview["errors"] = [f"Missing moment source file: moments/{source_path.name}"]
        return preview

    entry = build_moment_source_entry(source_path, moments_images_root=paths["moments_images_root"])
    preview.update(
        {
            "title": entry.get("title") or "",
            "status": entry.get("status") or "",
            "date": entry.get("date") or "",
            "date_display": entry.get("date_display") or "",
            "published_date": entry.get("published_date") or "",
            "image_file": entry.get("source_image_file") or "",
            "image_alt": entry.get("image_alt") or "",
        }
    )
    source_image_path = Path(str(entry.get("source_image_path") or "")).resolve() if entry.get("source_image_path") else None
    preview["source_image_path"] = (
        str(Path("moments") / "images" / Path(str(entry.get("source_image_file") or "")).name)
        if entry.get("source_image_file")
        else ""
    )
    preview["source_image_exists"] = bool(source_image_path and source_image_path.exists())
    preview["generated_page_exists"] = (repo_root / "_moments" / f"{moment_id}.md").exists()
    preview["generated_json_exists"] = (repo_root / "assets/moments/index" / f"{moment_id}.json").exists()
    preview["in_moments_index"] = False

    moments_index_path = repo_root / "assets/data/moments_index.json"
    if moments_index_path.exists():
        try:
            moments_index_text = moments_index_path.read_text(encoding="utf-8")
            payload = json.loads(moments_index_text)
            moments_map = payload.get("moments") if isinstance(payload, dict) else {}
            moment_index_ids = (
                {str(key).strip().lower() for key in moments_map.keys()}
                if isinstance(moments_map, dict)
                else set()
            )
            preview["in_moments_index"] = moment_id in moment_index_ids
            if not preview["in_moments_index"]:
                preview["in_moments_index"] = f'"{moment_id}":' in moments_index_text
        except Exception:
            preview["in_moments_index"] = False

    errors = validate_moment_source_entry(entry)
    preview["errors"] = errors
    preview["valid"] = not errors
    preview["effective_force"] = bool(entry.get("status") == "published")
    preview["summary"] = (
        f"Import moment {moment_id} from moments/{source_path.name}, rebuild the moment payloads, and rebuild catalogue search."
    )
    return preview


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
        "kind": "series",
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


def build_scope_for_moment(
    repo_root: Path,
    moment_file: str,
    *,
    force: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    preview = preview_moment_source(repo_root, moment_file, env=env)
    if not preview.get("valid"):
        errors = preview.get("errors") or []
        raise ValueError("; ".join(str(error) for error in errors) or "moment source preview failed")
    moment_id = str(preview.get("moment_id") or "").strip().lower()
    effective_force = bool(force) or bool(preview.get("effective_force"))
    return {
        "kind": "moment",
        "moment_ids": [moment_id],
        "moment_file": str(preview.get("moment_file") or ""),
        "work_ids": [],
        "series_ids": [],
        "generate_only": list(DEFAULT_MOMENT_ARTIFACTS),
        "rebuild_search": True,
        "search_scope": "catalogue",
        "source_mode": "moment-source",
        "summary": summarize_moment_scope([moment_id]),
        "effective_force": effective_force,
        "preview": preview,
    }


def summarize_scope(work_ids: Sequence[str], series_ids: Sequence[str]) -> str:
    work_text = ", ".join(work_ids) if work_ids else "none"
    series_text = ", ".join(series_ids) if series_ids else "none"
    return f"Build works [{work_text}], series [{series_text}], aggregate indexes, and catalogue search."


def summarize_moment_scope(moment_ids: Sequence[str]) -> str:
    moment_text = ", ".join(moment_ids) if moment_ids else "none"
    return f"Build moments [{moment_text}], rebuild the moments index, and rebuild catalogue search."


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
        "--internal-json-source-run",
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


def build_generate_moment_command(repo_root: Path, scope: Dict[str, Any], *, write: bool, force: bool) -> list[str]:
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "generate_work_pages.py"),
        "--only",
        "moments",
        "--moment-ids",
        ",".join(scope["moment_ids"]),
    ]
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
    scope_kind = str(scope.get("kind") or "work").strip().lower()
    effective_force = bool(scope.get("effective_force")) or bool(force)
    if scope_kind == "moment":
        commands = [
            ("Generate Moment Pages", build_generate_moment_command(repo_root, scope, write=write, force=effective_force)),
            ("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=effective_force, env=env)),
        ]
    else:
        commands = [
            ("Generate Work Pages", build_generate_command(repo_root, Path(scope["source_dir"]), scope, write=write, force=effective_force)),
            ("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=effective_force, env=env)),
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
        "force": effective_force,
        "steps": steps,
    }
    if failed_step:
        response["failed_step"] = failed_step
        response["error"] = failure_message

    if write and log_activity:
        if scope_kind == "moment":
            append_build_activity(
                repo_root,
                build_activity_entry_for_scoped_moment_build(
                    time_utc=utc_now(),
                    status=status,
                    moment_ids=scope.get("moment_ids", []),
                    failed_step=failed_step,
                    force=effective_force,
                ),
            )
        else:
            append_build_activity(
                repo_root,
                build_activity_entry_for_scoped_json_build(
                    time_utc=utc_now(),
                    status=status,
                    work_ids=scope["work_ids"],
                    series_ids=scope["series_ids"],
                    failed_step=failed_step,
                    force=effective_force,
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


def run_moment_scoped_build(
    repo_root: Path,
    *,
    moment_file: str,
    write: bool,
    force: bool = False,
    log_activity: bool = True,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    scope = build_scope_for_moment(repo_root, moment_file, force=force, env=env)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=scope.get("effective_force", force), log_activity=log_activity)


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


def build_activity_entry_for_scoped_moment_build(
    *,
    time_utc: str,
    status: str,
    moment_ids: Sequence[str],
    failed_step: str = "",
    force: bool = False,
) -> Dict[str, Any]:
    moment_ids_list = sorted(str(moment_id) for moment_id in moment_ids if str(moment_id).strip())
    summary = (
        f"Scoped moment build updated {len(moment_ids_list)} moment records and catalogue search."
        if status == "completed"
        else f"Scoped moment build failed for {len(moment_ids_list)} moment records."
    )
    first_id = moment_ids_list[0] if moment_ids_list else "none"
    return {
        "id": f"{time_utc}-build_catalogue_moment-{first_id}",
        "time_utc": time_utc,
        "script": "build_catalogue_moment",
        "status": status,
        "dry_run": False,
        "planner_mode": "moment-source-scoped",
        "summary": summary,
        "changes": {
            "source": {
                "works": [],
                "series": [],
                "work_details": [],
                "moments": moment_ids_list,
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
            "generate_moment_ids": len(moment_ids_list),
            "rebuild_search": True,
            "force_generate": bool(force),
        },
        "results": {
            "source_mode": "moment-source",
            "moment_ids": moment_ids_list,
            "failed_step": failed_step,
        },
    }


def print_preview(scope: Dict[str, Any], repo_root: Path, source_dir: Path, *, force: bool) -> None:
    print(scope["summary"])
    print(f"Source mode: {scope['source_mode']}")
    if scope.get("kind") == "moment":
        print(f"Moment IDs: {', '.join(scope['moment_ids']) if scope['moment_ids'] else 'none'}")
        print(f"Moment file: {scope.get('moment_file') or 'none'}")
    else:
        print(f"Work IDs: {', '.join(scope['work_ids']) if scope['work_ids'] else 'none'}")
        print(f"Series IDs: {', '.join(scope['series_ids']) if scope['series_ids'] else 'none'}")
    print(f"Search rebuild: {'yes' if scope['rebuild_search'] else 'no'}")
    print("Commands:")
    commands = (
        [
            build_generate_moment_command(repo_root, scope, write=False, force=bool(scope.get("effective_force")) or bool(force)),
            build_search_command(repo_root, write=False, force=bool(scope.get("effective_force")) or bool(force)),
        ]
        if scope.get("kind") == "moment"
        else [
            build_generate_command(repo_root, source_dir, scope, write=False, force=force),
            build_search_command(repo_root, write=False, force=force),
        ]
    )
    for cmd in commands:
        print("  + " + " ".join(cmd))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scoped JSON-source catalogue build helper.")
    parser.add_argument("--work-id", default="", help="Target work_id")
    parser.add_argument("--moment-file", default="", help="Target moment markdown filename, for example keys.md")
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
    work_id = str(args.work_id or "").strip()
    moment_file = str(args.moment_file or "").strip()
    if bool(work_id) == bool(moment_file):
        raise SystemExit("Pass exactly one of --work-id or --moment-file.")
    if moment_file:
        scope = build_scope_for_moment(repo_root, moment_file, force=args.force)
    else:
        scope = build_scope_for_work(source_dir, work_id, extra_series_ids=args.extra_series_ids.split(","))
    if not args.write:
        print_preview(scope, repo_root, source_dir, force=args.force)
        return

    result = (
        run_moment_scoped_build(
            repo_root,
            moment_file=moment_file,
            write=True,
            force=args.force,
            log_activity=True,
        )
        if moment_file
        else run_scoped_build(
            repo_root,
            source_dir=source_dir,
            work_id=work_id,
            extra_series_ids=args.extra_series_ids.split(","),
            write=True,
            force=args.force,
            log_activity=True,
        )
    )
    if result["status"] != "completed":
        raise SystemExit(str(result.get("error") or "Scoped JSON build failed."))
    print(scope["summary"])


if __name__ == "__main__":
    main()

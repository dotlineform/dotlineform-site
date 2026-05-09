#!/usr/bin/env python3
"""Scoped JSON-source catalogue build helper."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import catalogue_build_commands as build_commands
import catalogue_build_field_plan as build_field_plan
import catalogue_build_media as build_media
import catalogue_build_scopes as build_scopes
from catalogue_source import DEFAULT_SOURCE_DIR
from local_env import runtime_env
from moment_sources import (
    CATALOGUE_MOMENT_PROSE_REL_DIR,
    MOMENT_METADATA_FILENAME,
    moment_metadata_payload,
    normalize_moment_filename,
    validate_moment_metadata_record,
)
from pipeline_config import (
    load_pipeline_config,
    source_moments_images_subdir,
    source_moments_root_subdir,
)


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = build_media.PROJECTS_BASE_DIR_ENV_NAME
CATALOGUE_PROSE_STAGING_REL_DIR = build_media.CATALOGUE_PROSE_STAGING_REL_DIR
MOMENT_PROSE_STAGING_REL_DIR = build_media.MOMENT_PROSE_STAGING_REL_DIR
CATALOGUE_MEDIA_STAGING_REL_DIR = build_media.CATALOGUE_MEDIA_STAGING_REL_DIR

DEFAULT_ARTIFACTS = build_scopes.DEFAULT_ARTIFACTS
DEFAULT_MOMENT_ARTIFACTS = build_scopes.DEFAULT_MOMENT_ARTIFACTS


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def detect_projects_base_dir(env: Dict[str, str] | None = None) -> Path:
    return build_media.detect_projects_base_dir(env)


def detect_projects_base_dir_optional(env: Dict[str, str] | None = None) -> tuple[Path | None, str]:
    return build_media.detect_projects_base_dir_optional(env)


def display_source_path(path: Path | None, projects_base_dir: Path | None = None) -> str:
    return build_media.display_source_path(path, projects_base_dir)


def normalize_filename(value: Any) -> str:
    return build_media.normalize_filename(value)


def repo_relative_path(path: Path, repo_root: Path) -> str:
    return build_media.repo_relative_path(path, repo_root)


def resolve_work_media_source(records, work_id: str, *, env: Dict[str, str] | None = None) -> tuple[Path | None, str, Path | None, str]:
    return build_media.resolve_work_media_source(records, work_id, env=env)


def resolve_detail_media_source(records, detail_uid: str, *, env: Dict[str, str] | None = None) -> tuple[Path | None, str, Path | None, str]:
    return build_media.resolve_detail_media_source(records, detail_uid, env=env)


def resolve_moment_media_source(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> tuple[str, Path | None, str, Path | None, str]:
    return build_media.resolve_moment_media_source(repo_root, moment_file, metadata=metadata, env=env)


def build_local_media_plan(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    env: Dict[str, str] | None = None,
    force: bool = False,
) -> Dict[str, Any]:
    return build_media.build_local_media_plan(repo_root, scope=scope, env=env, force=force)


def run_ffmpeg_thumb(src: Path, size: int, dest: Path) -> tuple[int, str]:
    return build_media.run_ffmpeg_thumb(src, size, dest)


def run_ffmpeg_primary(src: Path, width: int, dest: Path) -> tuple[int, str]:
    return build_media.run_ffmpeg_primary(src, width, dest)


_DEFAULT_RUN_FFMPEG_THUMB_WRAPPER = run_ffmpeg_thumb
_DEFAULT_RUN_FFMPEG_PRIMARY_WRAPPER = run_ffmpeg_primary


def execute_local_media_plan(
    repo_root: Path,
    *,
    scope: Dict[str, Any],
    write: bool,
    env: Dict[str, str] | None = None,
    force: bool = False,
) -> Dict[str, Any]:
    thumb_runner = run_ffmpeg_thumb if run_ffmpeg_thumb is not _DEFAULT_RUN_FFMPEG_THUMB_WRAPPER else None
    primary_runner = run_ffmpeg_primary if run_ffmpeg_primary is not _DEFAULT_RUN_FFMPEG_PRIMARY_WRAPPER else None
    return build_media.execute_local_media_plan(
        repo_root,
        scope=scope,
        write=write,
        env=env,
        force=force,
        plan_builder=build_local_media_plan,
        thumb_runner=thumb_runner,
        primary_runner=primary_runner,
    )


def build_work_readiness(records, work_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    return build_media.build_work_readiness(records, work_id, env=env)


def build_series_readiness(records, series_id: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    return build_media.build_series_readiness(records, series_id, env=env)


def build_detail_readiness(records, detail_uid: str, *, env: Dict[str, str] | None = None) -> Dict[str, Any]:
    return build_media.build_detail_readiness(records, detail_uid, env=env)


def build_moment_readiness(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    return build_media.build_moment_readiness(repo_root, moment_file, metadata=metadata, env=env)


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


def build_moment_import_metadata(
    source_dir: Path,
    moment_id: str,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return build_scopes.build_moment_import_metadata(source_dir, moment_id, metadata)


def preview_moment_source(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    staged: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    filename = normalize_moment_filename(moment_file)
    moment_id = filename[:-3]
    source_dir = repo_root / DEFAULT_SOURCE_DIR
    staging_path = repo_root / MOMENT_PROSE_STAGING_REL_DIR / filename
    target_path = repo_root / CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    source_path = staging_path if staged else target_path
    source_rel_path = (MOMENT_PROSE_STAGING_REL_DIR if staged else CATALOGUE_MOMENT_PROSE_REL_DIR) / filename
    metadata_record = build_moment_import_metadata(source_dir, moment_id, metadata)
    preview: Dict[str, Any] = {
        "kind": "moment",
        "moment_id": moment_id,
        "moment_file": filename,
        "source_path": str(source_rel_path),
        "staging_path": str(MOMENT_PROSE_STAGING_REL_DIR / filename),
        "target_path": str(CATALOGUE_MOMENT_PROSE_REL_DIR / filename),
        "metadata_path": str(DEFAULT_SOURCE_DIR / MOMENT_METADATA_FILENAME),
        "public_url": f"/moments/{moment_id}/",
        "generated_page_path": str(Path("_moments") / f"{moment_id}.md"),
        "generated_json_path": str(Path("assets/moments/index") / f"{moment_id}.json"),
        "moments_index_path": "assets/data/moments_index.json",
        "search_scope": "catalogue",
        "source_exists": source_path.exists(),
        "target_exists": target_path.exists(),
        "errors": [],
        "valid": False,
        "title": metadata_record.get("title") or "",
        "status": metadata_record.get("status") or "",
        "date": metadata_record.get("date") or "",
        "date_display": metadata_record.get("date_display") or "",
        "published_date": metadata_record.get("published_date") or "",
        "image_file": metadata_record.get("source_image_file") or f"{moment_id}.jpg",
        "image_alt": metadata_record.get("image_alt") or "",
    }

    if not source_path.exists():
        preview["errors"] = [f"Missing {'staged ' if staged else ''}moment prose file: {source_rel_path}"]
        return preview

    projects_base_dir, _availability_error = detect_projects_base_dir_optional(env)
    source_image_file = str(metadata_record.get("source_image_file") or f"{moment_id}.jpg")
    source_image_path = (projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG) / source_image_file) if projects_base_dir else None
    preview["source_image_path"] = str(Path("moments") / "images" / Path(source_image_file).name)
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

    errors = validate_moment_metadata_record(metadata_record)
    preview["errors"] = errors
    preview["valid"] = not errors
    preview["effective_force"] = False
    preview["refresh_published"] = bool(metadata_record.get("status") == "published")
    source_label = MOMENT_PROSE_STAGING_REL_DIR / filename if staged else CATALOGUE_MOMENT_PROSE_REL_DIR / filename
    action = "Import" if staged else "Build"
    preview["summary"] = f"{action} moment {moment_id} from {source_label}, rebuild the moment payloads, and rebuild catalogue search."
    return preview


def normalize_series_ids(values: Iterable[Any]) -> list[str]:
    return build_scopes.normalize_series_ids(values)


def validate_buildable_series_scope(records, series_ids: Sequence[str]) -> None:
    build_scopes.validate_buildable_series_scope(records, series_ids)


def build_scope_for_work(
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    *,
    detail_uid: str = "",
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    return build_scopes.build_scope_for_work(
        source_dir,
        work_id,
        extra_series_ids=extra_series_ids,
        detail_uid=detail_uid,
        env=env,
        work_readiness_builder=build_work_readiness,
        detail_readiness_builder=build_detail_readiness,
    )


def build_scope_for_series(
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    *,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    return build_scopes.build_scope_for_series(
        source_dir,
        series_id,
        extra_work_ids=extra_work_ids,
        env=env,
        series_readiness_builder=build_series_readiness,
    )


def build_scope_for_moment(
    repo_root: Path,
    moment_file: str,
    *,
    metadata: Dict[str, Any] | None = None,
    force: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    return build_scopes.build_scope_for_moment(
        repo_root,
        moment_file,
        metadata=metadata,
        force=force,
        env=env,
        moment_preview_builder=preview_moment_source,
        moment_metadata_builder=build_moment_import_metadata,
        moment_readiness_builder=build_moment_readiness,
    )


def summarize_scope(work_ids: Sequence[str], series_ids: Sequence[str]) -> str:
    return build_scopes.summarize_scope(work_ids, series_ids)


def summarize_moment_scope(moment_ids: Sequence[str]) -> str:
    return build_scopes.summarize_moment_scope(moment_ids)


def parse_csv_tokens(value: Any) -> list[str]:
    return build_field_plan.parse_csv_tokens(value)


def infer_record_family_for_scope(scope: Mapping[str, Any], explicit_family: str = "") -> str:
    return build_field_plan.infer_record_family_for_scope(scope, explicit_family)


def build_field_plan_for_scope(
    repo_root: Path,
    source_dir: Path,
    scope: Mapping[str, Any],
    *,
    changed_fields: Sequence[str],
    record_family: str = "",
) -> Dict[str, Any]:
    return build_field_plan.build_field_plan_for_scope(
        repo_root,
        source_dir,
        scope,
        changed_fields=changed_fields,
        record_family=record_family,
    )


def apply_field_build_plan_to_scope(scope: Dict[str, Any], build_plan: Mapping[str, Any]) -> None:
    build_field_plan.apply_field_build_plan_to_scope(scope, build_plan)


def field_plan_explanation_lines(field_plan: Mapping[str, Any]) -> list[str]:
    return build_field_plan.field_plan_explanation_lines(field_plan)


def resolve_bundle_bin(env: Dict[str, str] | None = None) -> str:
    return build_commands.resolve_bundle_bin(env or runtime_env())


def build_generate_command(
    repo_root: Path,
    source_dir: Path,
    scope: Dict[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    return build_commands.build_generate_command(
        repo_root,
        source_dir,
        scope,
        write=write,
        force=force,
        refresh_published=refresh_published,
    )


def build_generate_moment_command(
    repo_root: Path,
    source_dir: Path,
    scope: Dict[str, Any],
    *,
    write: bool,
    force: bool,
    refresh_published: bool,
) -> list[str]:
    return build_commands.build_generate_moment_command(
        repo_root,
        source_dir,
        scope,
        write=write,
        force=force,
        refresh_published=refresh_published,
    )


def build_search_command(repo_root: Path, *, write: bool, force: bool, env: Dict[str, str] | None = None) -> list[str]:
    return build_commands.build_search_command(repo_root, write=write, force=force, env=env or runtime_env())


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
        media_step = execute_local_media_plan(repo_root, scope=scope, write=write, env=env, force=force)
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
                    build_generate_moment_command(
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
                    build_generate_command(
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
        commands.append(("Build Catalogue Search Index", build_search_command(repo_root, write=write, force=effective_force, env=env)))
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


def run_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    work_id: str,
    extra_series_ids: Sequence[Any] | None = None,
    detail_uid: str = "",
    write: bool,
    force: bool = False,
    media_only: bool = False,
) -> Dict[str, Any]:
    scope = build_scope_for_work(source_dir, work_id, extra_series_ids=extra_series_ids, detail_uid=detail_uid)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, media_only=media_only)


def run_series_scoped_build(
    repo_root: Path,
    *,
    source_dir: Path,
    series_id: str,
    extra_work_ids: Sequence[Any] | None = None,
    write: bool,
    force: bool = False,
    media_only: bool = False,
) -> Dict[str, Any]:
    scope = build_scope_for_series(source_dir, series_id, extra_work_ids=extra_work_ids)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, media_only=media_only)


def run_moment_scoped_build(
    repo_root: Path,
    *,
    moment_file: str,
    metadata: Dict[str, Any] | None = None,
    write: bool,
    force: bool = False,
    media_only: bool = False,
    env: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    scope = build_scope_for_moment(repo_root, moment_file, metadata=metadata, force=force, env=env)
    return run_scoped_build_scope(repo_root, scope=scope, write=write, force=force, media_only=media_only)


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
        explanation_lines = field_plan_explanation_lines(field_plan)
        if explanation_lines:
            print("Field-aware reasons:")
            for line in explanation_lines:
                print(f"  - {line}")
    media_plan = (
        build_local_media_plan(repo_root, scope=scope, force=force)
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
                build_generate_moment_command(
                    repo_root,
                    repo_root / DEFAULT_SOURCE_DIR,
                    scope,
                    write=False,
                    force=bool(force),
                    refresh_published=True,
                )
            )
        else:
            commands.append(build_generate_command(repo_root, source_dir, scope, write=False, force=force, refresh_published=True))
    if bool(scope.get("rebuild_search")):
        commands.append(build_search_command(repo_root, write=False, force=bool(force)))
    if commands:
        for cmd in commands:
            print("  + " + " ".join(cmd))
    else:
        print("  (none)")


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
    if sum(1 for value in (work_id, series_id, moment_file) if value) != 1:
        raise SystemExit("Pass exactly one of --work-id, --series-id, or --moment-file.")
    if moment_file:
        scope = build_scope_for_moment(repo_root, moment_file, force=args.force)
    elif series_id:
        scope = build_scope_for_series(source_dir, series_id, extra_work_ids=args.extra_work_ids.split(","))
    else:
        scope = build_scope_for_work(source_dir, work_id, extra_series_ids=args.extra_series_ids.split(","), detail_uid=args.detail_uid)
    changed_fields = parse_csv_tokens(args.changed_fields)
    if changed_fields:
        build_plan = build_field_plan_for_scope(
            repo_root,
            source_dir,
            scope,
            changed_fields=changed_fields,
            record_family=args.record_family,
        )
        apply_field_build_plan_to_scope(scope, build_plan)
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

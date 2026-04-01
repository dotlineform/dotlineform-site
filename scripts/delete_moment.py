#!/usr/bin/env python3
"""
Delete a single moment from canonical source files and generated artifacts.

Safe by default:
- dry-run unless you pass --write
- accepts exactly one --moment-id
- leaves canonical source files alone unless explicitly requested

Deletion scope:
- _moments/<moment_id>.md
- assets/moments/index/<moment_id>.json
- assets/moments/img/<moment_id>-thumb-*.*
- removes the moment from assets/data/moments_index.json
- removes local staged/srcset moment media under $DOTLINEFORM_MEDIA_BASE_DIR when configured
- rebuilds assets/data/search/catalogue/index.json

Optional source deletion:
- canonical source prose under <DOTLINEFORM_PROJECTS_BASE_DIR>/moments/<moment_id>.md
- canonical source image under <DOTLINEFORM_PROJECTS_BASE_DIR>/moments/images/<image_file>

Intentionally left untouched:
- remote moment media under media.dotlineform.com / R2
- unrelated repo artifacts
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:
    from display_paths import format_display_path
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.display_paths import format_display_path

try:
    from moment_sources import parse_front_matter
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.moment_sources import parse_front_matter

try:
    from pipeline_config import (
        env_var_name,
        env_var_value,
        load_pipeline_config,
        media_mode_input_subdir,
        media_mode_output_subdir,
        source_moments_images_subdir,
        source_moments_root_subdir,
    )
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.pipeline_config import (
        env_var_name,
        env_var_value,
        load_pipeline_config,
        media_mode_input_subdir,
        media_mode_output_subdir,
        source_moments_images_subdir,
        source_moments_root_subdir,
    )

try:
    from script_logging import append_script_log
except ModuleNotFoundError:  # pragma: no cover - package import fallback
    from scripts.script_logging import append_script_log


PIPELINE_CONFIG = load_pipeline_config(Path(__file__))
PROJECTS_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "projects_base_dir")
MEDIA_BASE_DIR_ENV_NAME = env_var_name(PIPELINE_CONFIG, "media_base_dir")
OUTPUT_FORMAT = str(PIPELINE_CONFIG["encoding"]["format"])
PRIMARY_SUBDIR = str(PIPELINE_CONFIG["variants"]["primary"]["output_subdir"])
THUMB_SUBDIR = str(PIPELINE_CONFIG["variants"]["thumb"]["output_subdir"])
MOMENT_ID_ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789-")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def normalize_moment_id(raw: str) -> str:
    value = normalize_text(raw).lower()
    if not value or value.startswith("-") or value.endswith("-") or "--" in value:
        raise SystemExit("--moment-id must be a single slug-safe moment_id")
    if any(ch not in MOMENT_ID_ALLOWED for ch in value):
        raise SystemExit("--moment-id must be a single slug-safe moment_id")
    return value


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def backup_stamp_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            out[str(key)] = canonicalize_for_hash(value[key])
        return out
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, float):
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return float(f"{value:.15g}")
    return value


def compute_payload_version(payload: Any) -> str:
    canonical = json.dumps(
        canonicalize_for_hash(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return f"blake2b-{hashlib.blake2b(canonical, digest_size=16).hexdigest()}"


def find_repo_root(explicit_root: str) -> Path:
    if explicit_root:
        repo_root = Path(explicit_root).expanduser().resolve()
        if not (repo_root / "_config.yml").exists():
            raise SystemExit(f"--repo-root does not look like repo root (missing _config.yml): {repo_root}")
        return repo_root

    for start in [Path.cwd(), Path(__file__).resolve().parent]:
        current = start.resolve()
        for candidate in [current, *current.parents]:
            if (candidate / "_config.yml").exists():
                return candidate
    raise SystemExit("Could not auto-detect repo root. Pass --repo-root.")


def log_event(event: str, details: Optional[Dict[str, Any]] = None) -> None:
    try:
        append_script_log(Path(__file__), event=event, details=details or {})
    except Exception:
        pass


def display_path(path: Path | str, *, repo_root: Path, projects_base_dir: Path | None, media_base_dir: Path | None) -> str:
    return format_display_path(
        path,
        repo_root=repo_root,
        projects_base_dir=projects_base_dir,
        media_base_dir=media_base_dir,
    )


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    ensure_parent(path)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def backup_existing_paths(
    paths: Iterable[Path],
    *,
    repo_root: Path,
    backup_root: Path,
    projects_base_dir: Path | None,
    media_base_dir: Path | None,
) -> Dict[Path, Path]:
    backups: Dict[Path, Path] = {}
    repo_root_resolved = repo_root.resolve()
    projects_resolved = projects_base_dir.resolve() if projects_base_dir is not None else None
    media_resolved = media_base_dir.resolve() if media_base_dir is not None else None
    for path in paths:
        if not path.exists() or path in backups:
            continue
        resolved = path.resolve()
        try:
            rel_path = Path("repo") / resolved.relative_to(repo_root_resolved)
        except ValueError:
            if projects_resolved is not None:
                try:
                    rel_path = Path("projects") / resolved.relative_to(projects_resolved)
                except ValueError:
                    rel_path = None
            else:
                rel_path = None
            if rel_path is None and media_resolved is not None:
                try:
                    rel_path = Path("media") / resolved.relative_to(media_resolved)
                except ValueError:
                    rel_path = None
            if rel_path is None:
                rel_path = Path("external") / path.name
        backup_path = backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        backups[path] = backup_path
    return backups


def restore_backups(backups: Dict[Path, Path]) -> None:
    for path, backup_path in backups.items():
        if not backup_path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, path)


def delete_paths(paths: Iterable[Path]) -> list[Path]:
    deleted: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        path.unlink()
        deleted.append(path)
    return deleted


def load_json_object(path: Path, label: str) -> Dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Failed to parse {label}: {path} ({exc})")
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid {label} payload (expected object): {path}")
    return payload


def finalize_moments_index_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    moments_map = payload.get("moments")
    if not isinstance(moments_map, dict):
        raise SystemExit("Invalid moments_index.json payload: missing moments map")
    schema = str((payload.get("header") or {}).get("schema") or "moments_index_v1")
    payload["header"] = {
        "schema": schema,
        "version": compute_payload_version({"schema": schema, "moments": moments_map}),
        "generated_at_utc": utc_now(),
        "count": len(moments_map),
    }
    return payload


def collect_matching_paths(root: Path, patterns: Iterable[str]) -> list[Path]:
    collected: list[Path] = []
    seen: set[Path] = set()
    if not root.exists():
        return collected
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            collected.append(path)
    return collected


def resolve_source_paths(moment_id: str, *, projects_base_dir: Path) -> tuple[Path, Path | None]:
    moments_root = projects_base_dir / source_moments_root_subdir(PIPELINE_CONFIG)
    moments_images_root = projects_base_dir / source_moments_images_subdir(PIPELINE_CONFIG)
    prose_path = moments_root / f"{moment_id}.md"
    image_path: Path | None = None
    if prose_path.exists():
        front_matter = parse_front_matter(prose_path)
        image_file = normalize_text(front_matter.get("image_file")) or f"{moment_id}.jpg"
        image_path = moments_images_root / image_file
    return prose_path, image_path


def collect_repo_artifacts(moment_id: str, *, repo_root: Path) -> list[Path]:
    artifacts = [
        repo_root / "_moments" / f"{moment_id}.md",
        repo_root / "assets" / "moments" / "index" / f"{moment_id}.json",
    ]
    artifacts.extend(
        collect_matching_paths(
            repo_root / "assets" / "moments" / "img",
            [f"{moment_id}-thumb-*.*"],
        )
    )
    return artifacts


def collect_local_media_artifacts(moment_id: str, *, media_base_dir: Path | None) -> list[Path]:
    if media_base_dir is None:
        return []
    moment_input_dir = media_base_dir / media_mode_input_subdir(PIPELINE_CONFIG, "moment")
    moment_output_dir = media_base_dir / media_mode_output_subdir(PIPELINE_CONFIG, "moment")
    paths: list[Path] = []
    paths.extend(collect_matching_paths(moment_input_dir, [f"{moment_id}.*"]))
    paths.extend(
        collect_matching_paths(
            moment_output_dir / PRIMARY_SUBDIR,
            [f"{moment_id}-primary-*.{OUTPUT_FORMAT}"],
        )
    )
    paths.extend(
        collect_matching_paths(
            moment_output_dir / THUMB_SUBDIR,
            [f"{moment_id}-thumb-*.{OUTPUT_FORMAT}"],
        )
    )
    return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="Delete a single moment from canonical source files and generated artifacts.")
    ap.add_argument("--moment-id", required=True, help="Single slug-safe moment_id")
    ap.add_argument("--write", action="store_true", help="Apply changes; omit for dry-run")
    ap.add_argument("--delete-source-prose", action="store_true", help="Also delete the canonical source prose file")
    ap.add_argument("--delete-source-image", action="store_true", help="Also delete the canonical source image resolved from moment front matter")
    ap.add_argument("--repo-root", default="", help="Override repo-root auto-detection")
    ap.add_argument(
        "--projects-base-dir",
        default=env_var_value(PIPELINE_CONFIG, "projects_base_dir"),
        help=f"Override canonical source base dir (defaults from {PROJECTS_BASE_DIR_ENV_NAME})",
    )
    ap.add_argument(
        "--media-base-dir",
        default=env_var_value(PIPELINE_CONFIG, "media_base_dir"),
        help=f"Override local media base dir (defaults from {MEDIA_BASE_DIR_ENV_NAME})",
    )
    args = ap.parse_args()

    moment_id = normalize_moment_id(args.moment_id)
    repo_root = find_repo_root(args.repo_root)
    projects_base_dir = Path(args.projects_base_dir).expanduser().resolve() if args.projects_base_dir else None
    media_base_dir = Path(args.media_base_dir).expanduser().resolve() if args.media_base_dir else None
    if projects_base_dir is None:
        raise SystemExit(f"Missing canonical source base dir. Set {PROJECTS_BASE_DIR_ENV_NAME} or pass --projects-base-dir.")

    prose_path, source_image_path = resolve_source_paths(moment_id, projects_base_dir=projects_base_dir)
    repo_artifacts = collect_repo_artifacts(moment_id, repo_root=repo_root)
    local_media_artifacts = collect_local_media_artifacts(moment_id, media_base_dir=media_base_dir)
    moments_index_path = repo_root / "assets" / "data" / "moments_index.json"
    search_script = repo_root / "scripts" / "build_search.rb"

    if not prose_path.exists() and not any(path.exists() for path in repo_artifacts):
        raise SystemExit(f"No source prose or generated repo artifacts found for moment_id {moment_id!r}")

    paths_to_delete: list[Path] = []
    if args.delete_source_prose and prose_path.exists():
        paths_to_delete.append(prose_path)
    if args.delete_source_image and source_image_path is not None and source_image_path.exists():
        paths_to_delete.append(source_image_path)
    paths_to_delete.extend(path for path in repo_artifacts if path.exists())
    paths_to_delete.extend(path for path in local_media_artifacts if path.exists())

    print(f"Moment: {moment_id}")
    if prose_path.exists():
        print(
            "Source prose: "
            + display_path(prose_path, repo_root=repo_root, projects_base_dir=projects_base_dir, media_base_dir=media_base_dir)
            + (" (delete enabled)" if args.delete_source_prose else " (left untouched)")
        )
    else:
        print("Source prose: missing")
    if source_image_path is not None:
        print(
            "Source image: "
            + display_path(source_image_path, repo_root=repo_root, projects_base_dir=projects_base_dir, media_base_dir=media_base_dir)
            + (" (delete enabled)" if args.delete_source_image else " (left untouched)")
        )
    print(f"Repo artifacts to delete: {sum(1 for path in repo_artifacts if path.exists())}")
    print(f"Local media artifacts to delete: {sum(1 for path in local_media_artifacts if path.exists())}")
    print("Moments index: remove entry from assets/data/moments_index.json")
    print("Catalogue search: rebuild assets/data/search/catalogue/index.json")

    if not args.write:
        print("Dry-run only. Re-run with --write to apply changes.")
        log_event(
            "delete_moment_dry_run",
            {
                "moment_id": moment_id,
                "delete_source_prose": bool(args.delete_source_prose),
                "delete_source_image": bool(args.delete_source_image),
                "repo_artifacts": len([p for p in repo_artifacts if p.exists()]),
                "local_media_artifacts": len([p for p in local_media_artifacts if p.exists()]),
            },
        )
        return 0

    backup_root = repo_root / "var" / "delete_moment" / "backups" / backup_stamp_now()
    backup_root.mkdir(parents=True, exist_ok=True)
    backups = backup_existing_paths(
        [*paths_to_delete, moments_index_path],
        repo_root=repo_root,
        backup_root=backup_root,
        projects_base_dir=projects_base_dir,
        media_base_dir=media_base_dir,
    )

    try:
        if moments_index_path.exists():
            moments_index_payload = load_json_object(moments_index_path, "moments_index.json")
            moments_map = moments_index_payload.get("moments")
            if not isinstance(moments_map, dict):
                raise SystemExit("Invalid moments_index.json payload: missing moments map")
            moments_map.pop(moment_id, None)
            write_json_atomic(moments_index_path, finalize_moments_index_payload(moments_index_payload))

        delete_paths(paths_to_delete)

        ruby = shutil.which("ruby") or shutil.which("/Users/dlf/.rbenv/shims/ruby")
        if ruby is None:
            raise SystemExit("Ruby not found in PATH; cannot rebuild catalogue search.")
        proc = subprocess.run(
            [ruby, str(search_script), "--scope", "catalogue", "--write"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            raise SystemExit(f"Failed to rebuild catalogue search:\n{detail}")
    except Exception:
        restore_backups(backups)
        raise

    print(f"Deleted moment {moment_id}.")
    print(f"Backups: {backup_root.relative_to(repo_root)}")
    log_event(
        "delete_moment_write",
        {
            "moment_id": moment_id,
            "delete_source_prose": bool(args.delete_source_prose),
            "delete_source_image": bool(args.delete_source_image),
            "deleted_paths": len(paths_to_delete),
            "backup_root": str(backup_root.relative_to(repo_root)),
        },
    )
    return 0


if __name__ == "__main__":
    log_event("delete_moment_start", {"argv": sys.argv[1:]})
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        log_event("delete_moment_exit", {"status": "system_exit", "code": code})
        raise
    except Exception as exc:  # noqa: BLE001
        log_event("delete_moment_exit", {"status": "error", "error": str(exc)})
        raise

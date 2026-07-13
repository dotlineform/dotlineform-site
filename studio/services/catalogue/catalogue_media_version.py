"""Promote confirmed catalogue media versions after complete remote uploads."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from catalogue import catalogue_transactions as transactions
from catalogue.catalogue_build_commands import build_generate_command
from catalogue.catalogue_public_paths import WORKS_JSON_DIR
from catalogue.catalogue_source import (
    DEFAULT_SOURCE_DIR,
    SOURCE_FILES,
    is_empty,
    normalize_optional_int,
    payload_for_map,
    records_from_json_source,
    work_detail_record_payload_for_work,
    work_detail_source_path,
)
from local_env import runtime_env


MEDIA_KINDS = frozenset({"works", "work_details"})
BuildRunner = Callable[[Sequence[str], Path, Mapping[str, str]], tuple[int, str, str]]


@dataclass(frozen=True)
class MediaVersionFinalization:
    kind: str
    item_id: str
    work_id: str
    previous_version: int
    media_version: int
    advanced: bool
    source_path: str
    public_json_path: str
    build_stdout: str = ""


def _tail(value: str, limit: int = 8) -> str:
    return "\n".join(str(value or "").strip().splitlines()[-limit:])


def _default_build_runner(command: Sequence[str], repo_root: Path, env: Mapping[str, str]) -> tuple[int, str, str]:
    result = subprocess.run(
        list(command),
        cwd=str(repo_root),
        env=dict(env),
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode, result.stdout or "", result.stderr or ""


def _confirmed_version(record: Mapping[str, Any], *, kind: str, item_id: str) -> int:
    if is_empty(record.get("project_filename")):
        raise ValueError(f"{kind} {item_id}: project_filename is required before media-version promotion")
    version = normalize_optional_int(record.get("media_version"))
    if version is None or version < 1:
        raise ValueError(f"{kind} {item_id}: media_version must be a positive whole number")
    return version


def _source_update(
    repo_root: Path,
    *,
    kind: str,
    item_id: str,
    advance: bool,
) -> tuple[str, int, int, Path, Mapping[str, Any] | None]:
    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    records = records_from_json_source(source_dir)
    if kind == "works":
        record = records.works.get(item_id)
        if not isinstance(record, Mapping):
            raise ValueError(f"work_id not found: {item_id}")
        work_id = item_id
        source_path = (source_dir / SOURCE_FILES["works"]).resolve()
        previous_version = _confirmed_version(record, kind=kind, item_id=item_id)
        if not advance:
            return work_id, previous_version, previous_version, source_path, None
        next_works = {key: dict(value) for key, value in records.works.items()}
        next_record = dict(record)
        next_record["media_version"] = previous_version + 1
        next_works[item_id] = next_record
        return work_id, previous_version, previous_version + 1, source_path, payload_for_map("works", next_works)

    if kind == "work_details":
        record = records.work_details.get(item_id)
        if not isinstance(record, Mapping):
            raise ValueError(f"detail_uid not found: {item_id}")
        work_id = str(record.get("work_id") or "").strip()
        source_path = work_detail_source_path(source_dir, work_id).resolve()
        previous_version = _confirmed_version(record, kind=kind, item_id=item_id)
        if not advance:
            return work_id, previous_version, previous_version, source_path, None
        next_details = {key: dict(value) for key, value in records.work_details.items()}
        next_record = dict(record)
        next_record["media_version"] = previous_version + 1
        next_details[item_id] = next_record
        payload = work_detail_record_payload_for_work(
            work_id,
            records.work_detail_sections,
            next_details,
        )
        return work_id, previous_version, previous_version + 1, source_path, payload

    raise ValueError(f"unsupported catalogue media kind: {kind}")


def _build_work_json(
    repo_root: Path,
    *,
    work_id: str,
    build_runner: BuildRunner,
) -> str:
    source_dir = (repo_root / DEFAULT_SOURCE_DIR).resolve()
    scope = {
        "work_ids": [work_id],
        "series_ids": [],
        "generate_only": ["work-json"],
    }
    command = build_generate_command(
        repo_root,
        source_dir,
        scope,
        write=True,
        force=False,
        refresh_published=False,
        skip_source_dimension_refresh=True,
    )
    returncode, stdout, stderr = build_runner(command, repo_root, runtime_env(repo_root=repo_root))
    if returncode != 0:
        detail = _tail(stderr) or _tail(stdout) or f"focused work JSON build failed with exit code {returncode}"
        raise RuntimeError(detail)
    return _tail(stdout)


def finalize_catalogue_media_version(
    repo_root: Path,
    *,
    kind: str,
    item_id: str,
    advance: bool,
    build_runner: BuildRunner | None = None,
) -> MediaVersionFinalization:
    """Advance once after uploaded bytes changed, then rebuild the owning work JSON."""

    if kind not in MEDIA_KINDS:
        raise ValueError(f"unsupported catalogue media kind: {kind}")
    resolved_root = repo_root.resolve()
    work_id, previous_version, media_version, source_path, payload = _source_update(
        resolved_root,
        kind=kind,
        item_id=item_id,
        advance=advance,
    )
    if payload is not None:
        transactions.execute_source_json_write(
            {source_path: payload},
            dry_run=False,
            repo_root=resolved_root,
        )
    build_stdout = _build_work_json(
        resolved_root,
        work_id=work_id,
        build_runner=build_runner or _default_build_runner,
    )
    public_json_path = (WORKS_JSON_DIR / f"{work_id}.json").as_posix()
    try:
        source_display = source_path.relative_to(resolved_root).as_posix()
    except ValueError:
        source_display = source_path.name
    return MediaVersionFinalization(
        kind=kind,
        item_id=item_id,
        work_id=work_id,
        previous_version=previous_version,
        media_version=media_version,
        advanced=advance,
        source_path=source_display,
        public_json_path=public_json_path,
        build_stdout=build_stdout,
    )

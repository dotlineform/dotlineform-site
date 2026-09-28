"""Shared context and plumbing for Local Studio catalogue service routes."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, load_json_file
from catalogue.catalogue_galleries import GALLERIES_FILE, MEMBERSHIPS_FILE
from script_logging import append_script_log


LOGS_REL_DIR = Path("var/studio/catalogue/logs")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class CatalogueWriteContext:
    repo_root: Path
    source_dir: Path
    works_path: Path
    series_path: Path
    allowed_write_paths: set[Path]
    allowed_write_roots: set[Path]
    dry_run: bool = False


def build_catalogue_write_context(repo_root: Path, *, dry_run: bool = False) -> CatalogueWriteContext:
    resolved_root = repo_root.resolve()
    source_dir = (resolved_root / DEFAULT_SOURCE_DIR).resolve()
    return CatalogueWriteContext(
        repo_root=resolved_root,
        source_dir=source_dir,
        works_path=(source_dir / SOURCE_FILES["works"]).resolve(),
        series_path=(source_dir / SOURCE_FILES["series"]).resolve(),
        allowed_write_paths={
            (source_dir / filename).resolve()
            for kind, filename in SOURCE_FILES.items()
            if kind in {"works", "series"}
        } | {(source_dir / filename).resolve() for filename in (GALLERIES_FILE, MEMBERSHIPS_FILE)},
        allowed_write_roots=set(),
        dry_run=dry_run,
    )


def load_works_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    works = payload.get("works")
    if not isinstance(works, dict):
        raise ValueError("works source file must include a works object")
    return payload


def load_series_payload(path: Path) -> dict[str, Any]:
    payload = load_json_file(path)
    series = payload.get("series")
    if not isinstance(series, dict):
        raise ValueError("series source file must include a series object")
    return payload


def log_event(repo_root: Path, event: str, details: Mapping[str, Any] | None = None) -> None:
    try:
        append_script_log(
            Path(__file__),
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        pass

#!/usr/bin/env python3
"""Project canonical Docs Viewer runtime code into the tracked public site."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any, Sequence


SCHEMA_VERSION = "site_code_update_v1"
TOOL_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TOOL_ROOT.parent
DEFAULT_MANIFEST_PATH = TOOL_ROOT / "config" / "site-code-update.json"


class SiteCodeUpdateError(ValueError):
    """Raised when the projection manifest or an owned path is unsafe."""


@dataclass(frozen=True)
class ProjectionPolicy:
    source_root: str
    destination_root: str
    suffix: str
    complete_source: bool = False
    exact_files: frozenset[str] | None = None


PROJECTION_POLICIES = {
    "docs-viewer-public-js": ProjectionPolicy(
        source_root="docs-viewer/runtime/js/public",
        destination_root="site/docs-viewer/runtime/js/public",
        suffix=".js",
        complete_source=True,
    ),
    "docs-viewer-shared-js": ProjectionPolicy(
        source_root="docs-viewer/runtime/js/shared",
        destination_root="site/docs-viewer/runtime/js/shared",
        suffix=".js",
        complete_source=True,
    ),
    "docs-viewer-public-report-js": ProjectionPolicy(
        source_root="docs-viewer/runtime/js/reports",
        destination_root="site/docs-viewer/runtime/js/reports",
        suffix=".js",
        exact_files=frozenset({"docs-viewer-public-reports.js"}),
    ),
    "docs-viewer-shared-css": ProjectionPolicy(
        source_root="docs-viewer/static/css",
        destination_root="site/docs-viewer/static/css",
        suffix=".css",
        exact_files=frozenset(
            {
                "docs-viewer-reports.css",
                "docs-viewer-theme.css",
                "docs-viewer.css",
            }
        ),
    ),
}


@dataclass(frozen=True)
class Projection:
    projection_id: str
    source_root: str
    destination_root: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class PlannedCopy:
    source: str
    target: str


@dataclass(frozen=True)
class SiteCodeUpdatePlan:
    added: tuple[PlannedCopy, ...]
    changed: tuple[PlannedCopy, ...]
    removed: tuple[str, ...]
    unchanged: tuple[str, ...]

    @property
    def drift_count(self) -> int:
        return len(self.added) + len(self.changed) + len(self.removed)


def _relative_path(value: Any, label: str, *, filename: bool = False) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise SiteCodeUpdateError(f"{label} must be a non-empty POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise SiteCodeUpdateError(f"{label} must stay within the repository: {value!r}")
    normalized = path.as_posix()
    if normalized != value:
        raise SiteCodeUpdateError(f"{label} must be normalized: {value!r}")
    if filename and len(path.parts) != 1:
        raise SiteCodeUpdateError(f"{label} must be a filename without directories: {value!r}")
    return normalized


def _repo_path(repo_root: Path, relative: str, label: str) -> Path:
    path = repo_root.joinpath(*PurePosixPath(relative).parts)
    current = repo_root
    for part in PurePosixPath(relative).parts:
        current = current / part
        if current.is_symlink():
            raise SiteCodeUpdateError(f"{label} must not traverse a symlink: {relative}")
    return path


def _projection_record(raw: Any, index: int) -> Projection:
    label = f"projections[{index}]"
    if not isinstance(raw, dict):
        raise SiteCodeUpdateError(f"{label} must be an object")
    projection_id = raw.get("id")
    if not isinstance(projection_id, str) or not projection_id:
        raise SiteCodeUpdateError(f"{label}.id must be a non-empty string")
    policy = PROJECTION_POLICIES.get(projection_id)
    if policy is None:
        raise SiteCodeUpdateError(f"unsupported projection id: {projection_id}")
    source_root = _relative_path(raw.get("source_root"), f"{label}.source_root")
    destination_root = _relative_path(
        raw.get("destination_root"),
        f"{label}.destination_root",
    )
    if source_root != policy.source_root or destination_root != policy.destination_root:
        raise SiteCodeUpdateError(
            f"{projection_id} must map {policy.source_root} to {policy.destination_root}"
        )
    raw_files = raw.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise SiteCodeUpdateError(f"{label}.files must be a non-empty list")
    files = tuple(
        _relative_path(value, f"{label}.files[{file_index}]", filename=True)
        for file_index, value in enumerate(raw_files)
    )
    if files != tuple(sorted(files)) or len(files) != len(set(files)):
        raise SiteCodeUpdateError(f"{projection_id} files must be unique and sorted")
    if any(Path(filename).suffix != policy.suffix for filename in files):
        raise SiteCodeUpdateError(
            f"{projection_id} may contain only {policy.suffix} files"
        )
    if policy.exact_files is not None and frozenset(files) != policy.exact_files:
        expected = ", ".join(sorted(policy.exact_files))
        raise SiteCodeUpdateError(f"{projection_id} must list exactly: {expected}")
    return Projection(
        projection_id=projection_id,
        source_root=source_root,
        destination_root=destination_root,
        files=files,
    )


def load_manifest(repo_root: Path, manifest_path: Path) -> tuple[Projection, ...]:
    """Load the one allowed runtime projection and validate every source file."""

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SiteCodeUpdateError(f"could not load site-code manifest: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise SiteCodeUpdateError(
            f"site-code manifest schema_version must be {SCHEMA_VERSION}"
        )
    raw_projections = payload.get("projections")
    if not isinstance(raw_projections, list):
        raise SiteCodeUpdateError("site-code manifest projections must be a list")
    projections = tuple(
        _projection_record(raw, index) for index, raw in enumerate(raw_projections)
    )
    projection_ids = tuple(projection.projection_id for projection in projections)
    if projection_ids != tuple(PROJECTION_POLICIES):
        raise SiteCodeUpdateError(
            "site-code manifest must contain each supported projection once in canonical order"
        )

    seen_targets: set[str] = set()
    for projection in projections:
        policy = PROJECTION_POLICIES[projection.projection_id]
        source_root = _repo_path(repo_root, projection.source_root, projection.projection_id)
        if not source_root.is_dir():
            raise SiteCodeUpdateError(
                f"projection source root does not exist: {projection.source_root}"
            )
        if policy.complete_source:
            actual_entries = sorted(path.name for path in source_root.iterdir())
            if any(not path.is_file() or path.is_symlink() for path in source_root.iterdir()):
                raise SiteCodeUpdateError(
                    f"complete projection source must contain ordinary files only: {projection.source_root}"
                )
            if tuple(actual_entries) != projection.files:
                raise SiteCodeUpdateError(
                    f"{projection.projection_id} manifest does not match its complete source inventory"
                )
        for filename in projection.files:
            source_relative = f"{projection.source_root}/{filename}"
            source_path = _repo_path(repo_root, source_relative, projection.projection_id)
            if source_path.is_symlink() or not source_path.is_file():
                raise SiteCodeUpdateError(
                    f"projection source must be an ordinary file: {source_relative}"
                )
            target_relative = f"{projection.destination_root}/{filename}"
            if target_relative in seen_targets:
                raise SiteCodeUpdateError(f"duplicate projection target: {target_relative}")
            seen_targets.add(target_relative)
    return projections


def plan_site_code_update(
    repo_root: Path,
    projections: Sequence[Projection],
) -> SiteCodeUpdatePlan:
    """Compare canonical bytes with only the destinations owned by the manifest."""

    added: list[PlannedCopy] = []
    changed: list[PlannedCopy] = []
    removed: list[str] = []
    unchanged: list[str] = []
    for projection in projections:
        expected = set(projection.files)
        destination_root = _repo_path(
            repo_root,
            projection.destination_root,
            projection.projection_id,
        )
        if destination_root.exists() and not destination_root.is_dir():
            raise SiteCodeUpdateError(
                f"projection destination is not a directory: {projection.destination_root}"
            )
        if destination_root.is_dir():
            for target_path in sorted(destination_root.iterdir(), key=lambda path: path.name):
                if target_path.is_symlink() or not target_path.is_file():
                    raise SiteCodeUpdateError(
                        f"projection destination contains an unsupported entry: "
                        f"{target_path.relative_to(repo_root).as_posix()}"
                    )
                if target_path.name not in expected:
                    removed.append(target_path.relative_to(repo_root).as_posix())
        for filename in projection.files:
            source_relative = f"{projection.source_root}/{filename}"
            target_relative = f"{projection.destination_root}/{filename}"
            source_path = _repo_path(repo_root, source_relative, projection.projection_id)
            target_path = _repo_path(repo_root, target_relative, projection.projection_id)
            copy = PlannedCopy(source=source_relative, target=target_relative)
            if not target_path.exists():
                added.append(copy)
            elif not target_path.is_file():
                raise SiteCodeUpdateError(f"projection target is not a file: {target_relative}")
            elif source_path.read_bytes() != target_path.read_bytes():
                changed.append(copy)
            else:
                unchanged.append(target_relative)
    return SiteCodeUpdatePlan(
        added=tuple(sorted(added, key=lambda item: item.target)),
        changed=tuple(sorted(changed, key=lambda item: item.target)),
        removed=tuple(sorted(removed)),
        unchanged=tuple(sorted(unchanged)),
    )


def _ensure_directory(repo_root: Path, directory: Path) -> None:
    relative = directory.relative_to(repo_root)
    current = repo_root
    for part in relative.parts:
        current = current / part
        if current.exists():
            if current.is_symlink() or not current.is_dir():
                raise SiteCodeUpdateError(
                    f"projection destination parent is unsafe: "
                    f"{current.relative_to(repo_root).as_posix()}"
                )
        else:
            current.mkdir()


def _copy_file_atomic(repo_root: Path, item: PlannedCopy) -> None:
    source = _repo_path(repo_root, item.source, "projection source")
    target = _repo_path(repo_root, item.target, "projection target")
    _ensure_directory(repo_root, target.parent)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.",
        dir=target.parent,
    )
    os.close(descriptor)
    temp_path = Path(temp_name)
    try:
        shutil.copyfile(source, temp_path)
        shutil.copymode(source, temp_path)
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)


def apply_site_code_update(repo_root: Path, plan: SiteCodeUpdatePlan) -> None:
    """Apply one planned projection with atomic file replacement and bounded deletes."""

    for item in (*plan.added, *plan.changed):
        _copy_file_atomic(repo_root, item)
    for relative in plan.removed:
        target = _repo_path(repo_root, relative, "stale projection target")
        if target.is_symlink() or not target.is_file():
            raise SiteCodeUpdateError(f"stale projection target is unsafe: {relative}")
        target.unlink()


def _print_changes(plan: SiteCodeUpdatePlan) -> None:
    for item in plan.added:
        print(f"add {item.target}")
    for item in plan.changed:
        print(f"change {item.target}")
    for target in plan.removed:
        print(f"remove {target}")


def _summary(plan: SiteCodeUpdatePlan) -> str:
    return (
        f"{len(plan.added)} added, {len(plan.changed)} changed, "
        f"{len(plan.removed)} removed, {len(plan.unchanged)} unchanged"
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report drift without writing.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = repo_root / manifest_path
    try:
        projections = load_manifest(repo_root, manifest_path)
        plan = plan_site_code_update(repo_root, projections)
        _print_changes(plan)
        if args.check:
            if plan.drift_count:
                print(f"Site code projection is stale: {_summary(plan)}", file=sys.stderr)
                return 1
            print(f"Site code projection is current: {_summary(plan)}")
            return 0
        apply_site_code_update(repo_root, plan)
        print(f"Site code update complete: {_summary(plan)}")
        return 0
    except (OSError, SiteCodeUpdateError) as exc:
        print(f"site code update failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

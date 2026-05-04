#!/usr/bin/env python3
"""Prune local Studio backup files with newest-N-per-target retention."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


STUDIO_BACKUPS_REL_DIR = Path("var/studio/backups")
CATALOGUE_BACKUPS_REL_DIR = Path("var/studio/catalogue/backups")
DEFAULT_STUDIO_KEEP_PER_TARGET = 20
DEFAULT_CATALOGUE_KEEP_PER_TARGET = 30
IGNORED_BACKUP_NAMES = {".DS_Store"}

@dataclass(frozen=True)
class BackupItem:
    path: Path
    timestamp_key: str
    targets: tuple[str, ...]
    size_bytes: int
    kind: str


@dataclass
class RetentionPlan:
    keep: list[BackupItem] = field(default_factory=list)
    delete: list[BackupItem] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    missing_roots: list[Path] = field(default_factory=list)

    def extend(self, other: "RetentionPlan") -> None:
        self.keep.extend(other.keep)
        self.delete.extend(other.delete)
        self.skipped.extend(other.skipped)
        self.missing_roots.extend(other.missing_roots)


def detect_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "_config.yml").exists():
            return candidate
    raise ValueError("Could not detect repo root.")


def parse_timestamp_key(raw_name: str) -> str | None:
    parts = raw_name.rsplit("-", 3)
    if len(parts) >= 4:
        date_part, time_part, fraction_part = parts[-3], parts[-2], parts[-1]
        if (
            len(date_part) == 8
            and date_part.isdigit()
            and len(time_part) == 6
            and time_part.isdigit()
            and len(fraction_part) == 6
            and fraction_part.isdigit()
        ):
            return f"{date_part}-{time_part}-{fraction_part}"

    parts = raw_name.rsplit("-", 2)
    if len(parts) >= 3:
        date_part, time_part = parts[-2], parts[-1]
        if len(date_part) == 8 and date_part.isdigit() and len(time_part) == 6 and time_part.isdigit():
            return f"{date_part}-{time_part}"
    return None


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def tree_size(path: Path) -> int:
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += file_size(child)
    return total


def format_bytes(value: int) -> str:
    units = ("B", "K", "M", "G")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)}B"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{value}B"


def studio_target_for_backup(path: Path) -> str | None:
    marker = ".bak-"
    name = path.name
    if marker not in name:
        return None
    return name.split(marker, 1)[0]


def catalogue_target_for_bundle_file(bundle_root: Path, file_path: Path) -> str | None:
    try:
        rel = file_path.relative_to(bundle_root)
    except ValueError:
        return None
    parts = rel.parts
    if not parts:
        return None
    if parts[0] == "repo" and len(parts) > 1:
        return str(Path(*parts[1:])).replace("\\", "/")
    if len(parts) == 1 and file_path.suffix == ".json":
        return str(Path("assets/studio/data/catalogue") / file_path.name).replace("\\", "/")
    return str(rel).replace("\\", "/")


def collect_studio_backups(repo_root: Path) -> RetentionPlan:
    root = repo_root / STUDIO_BACKUPS_REL_DIR
    plan = RetentionPlan()
    if not root.exists():
        plan.missing_roots.append(root)
        return plan

    for path in sorted(root.iterdir()):
        if path.name in IGNORED_BACKUP_NAMES:
            continue
        if not path.is_file():
            plan.skipped.append(path)
            continue
        timestamp_key = parse_timestamp_key(path.name)
        target = studio_target_for_backup(path)
        if timestamp_key is None or target is None:
            plan.skipped.append(path)
            continue
        plan.keep.append(
            BackupItem(
                path=path,
                timestamp_key=timestamp_key,
                targets=(target,),
                size_bytes=file_size(path),
                kind="studio",
            )
        )
    return plan


def collect_catalogue_backups(repo_root: Path) -> RetentionPlan:
    root = repo_root / CATALOGUE_BACKUPS_REL_DIR
    plan = RetentionPlan()
    if not root.exists():
        plan.missing_roots.append(root)
        return plan

    for path in sorted(root.iterdir()):
        if path.name in IGNORED_BACKUP_NAMES:
            continue
        if not path.is_dir():
            plan.skipped.append(path)
            continue
        timestamp_key = parse_timestamp_key(path.name)
        if timestamp_key is None:
            plan.skipped.append(path)
            continue
        targets = sorted(
            {
                target
                for file_path in path.rglob("*")
                if file_path.is_file()
                for target in [catalogue_target_for_bundle_file(path, file_path)]
                if target
            }
        )
        if not targets:
            plan.skipped.append(path)
            continue
        plan.keep.append(
            BackupItem(
                path=path,
                timestamp_key=timestamp_key,
                targets=tuple(targets),
                size_bytes=tree_size(path),
                kind="catalogue",
            )
        )
    return plan


def split_retention(items: Iterable[BackupItem], keep_per_target: int) -> tuple[list[BackupItem], list[BackupItem]]:
    target_rankings: dict[str, set[Path]] = {}
    for item in items:
        for target in item.targets:
            target_rankings.setdefault(target, set())

    for target in target_rankings:
        target_items = [item for item in items if target in item.targets]
        target_items.sort(key=lambda item: (item.timestamp_key, str(item.path)), reverse=True)
        target_rankings[target] = {item.path for item in target_items[:keep_per_target]}

    keep: list[BackupItem] = []
    delete: list[BackupItem] = []
    for item in items:
        if any(item.path in target_rankings[target] for target in item.targets):
            keep.append(item)
        else:
            delete.append(item)
    keep.sort(key=lambda item: (item.kind, item.timestamp_key, str(item.path)), reverse=True)
    delete.sort(key=lambda item: (item.kind, item.timestamp_key, str(item.path)), reverse=True)
    return keep, delete


def build_retention_plan(repo_root: Path, *, studio_keep: int, catalogue_keep: int) -> RetentionPlan:
    final = RetentionPlan()

    studio_collected = collect_studio_backups(repo_root)
    studio_keep_items, studio_delete_items = split_retention(studio_collected.keep, studio_keep)
    final.keep.extend(studio_keep_items)
    final.delete.extend(studio_delete_items)
    final.skipped.extend(studio_collected.skipped)
    final.missing_roots.extend(studio_collected.missing_roots)

    catalogue_collected = collect_catalogue_backups(repo_root)
    catalogue_keep_items, catalogue_delete_items = split_retention(catalogue_collected.keep, catalogue_keep)
    final.keep.extend(catalogue_keep_items)
    final.delete.extend(catalogue_delete_items)
    final.skipped.extend(catalogue_collected.skipped)
    final.missing_roots.extend(catalogue_collected.missing_roots)
    return final


def delete_items(items: Iterable[BackupItem]) -> list[tuple[Path, str]]:
    failures: list[tuple[Path, str]] = []
    for item in items:
        try:
            if item.path.is_dir():
                shutil.rmtree(item.path)
            elif item.path.exists():
                item.path.unlink()
        except OSError as exc:
            failures.append((item.path, str(exc)))
    return failures


def summarize_kind(plan: RetentionPlan, kind: str) -> dict[str, int]:
    keep = [item for item in plan.keep if item.kind == kind]
    delete = [item for item in plan.delete if item.kind == kind]
    return {
        "kept": len(keep),
        "delete": len(delete),
        "delete_bytes": sum(item.size_bytes for item in delete),
    }


def relative_display(repo_root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def print_summary(repo_root: Path, plan: RetentionPlan, *, write: bool, quiet: bool, failures: list[tuple[Path, str]]) -> None:
    if quiet and not plan.delete and not plan.skipped and not failures:
        return

    mode = "Deleted" if write else "Would delete"
    studio = summarize_kind(plan, "studio")
    catalogue = summarize_kind(plan, "catalogue")
    print("Studio backup retention:")
    print(f"  studio kept: {studio['kept']}; {mode.lower()}: {studio['delete']} ({format_bytes(studio['delete_bytes'])})")
    print(
        f"  catalogue kept: {catalogue['kept']}; "
        f"{mode.lower()}: {catalogue['delete']} ({format_bytes(catalogue['delete_bytes'])})"
    )
    if plan.skipped:
        print(f"  skipped unparseable: {len(plan.skipped)}")
        if not quiet:
            for path in plan.skipped[:10]:
                print(f"    - {relative_display(repo_root, path)}")
    if plan.missing_roots and not quiet:
        print(f"  missing roots: {len(plan.missing_roots)}")
        for path in plan.missing_roots:
            print(f"    - {relative_display(repo_root, path)}")
    if failures:
        print(f"  delete failures: {len(failures)}")
        for path, error in failures[:10]:
            print(f"    - {relative_display(repo_root, path)}: {error}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview retention cleanup without deleting files.")
    mode.add_argument("--write", action="store_true", help="Delete backups outside the retention set.")
    parser.add_argument("--studio-keep", type=int, default=DEFAULT_STUDIO_KEEP_PER_TARGET)
    parser.add_argument("--catalogue-keep", type=int, default=DEFAULT_CATALOGUE_KEEP_PER_TARGET)
    parser.add_argument("--quiet", action="store_true", help="Print only actionable summaries.")
    parser.add_argument("--repo-root", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.studio_keep < 1 or args.catalogue_keep < 1:
        print("ERROR: retention counts must be positive integers.")
        return 2

    repo_root = (args.repo_root.expanduser().resolve() if args.repo_root else detect_repo_root())
    write = bool(args.write)
    plan = build_retention_plan(repo_root, studio_keep=args.studio_keep, catalogue_keep=args.catalogue_keep)
    failures = delete_items(plan.delete) if write else []
    print_summary(repo_root, plan, write=write, quiet=bool(args.quiet), failures=failures)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Resolve Admin checks target-map rules against repo files."""

from __future__ import annotations

import collections
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

SOURCE_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".liquid",
    ".md",
    ".py",
    ".rb",
    ".scss",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SOURCE_FILENAMES = {
    "Gemfile",
    "Gemfile.lock",
    "Rakefile",
    "Makefile",
}

GLOBAL_EXCLUDE_RULES: tuple[tuple[str, str], ...] = (
    (".git/", "dependency-cache"),
    (".jekyll-cache/", "cache"),
    (".pytest_cache/", "cache"),
    (".ruff_cache/", "cache"),
    (".vscode/", "local-editor"),
    ("_site/", "build-output"),
    ("node_modules/", "dependency-cache"),
    ("vendor/", "dependency-cache"),
    ("var/", "local-output"),
    ("logs/", "local-output"),
    ("docs-viewer/generated/", "generated-output"),
    ("assets/data/", "generated-output"),
    ("studio/data/generated/", "generated-output"),
    ("studio/data/canonical/", "canonical-data"),
    ("studio/retired/", "retired-prior-art"),
    ("analytics-app/data/canonical/", "canonical-data"),
)
GLOBAL_EXCLUDE_PARTS = {
    "__pycache__": "cache",
}


@dataclass(frozen=True)
class TargetRule:
    target_type: str
    target_id: str
    label: str
    include: tuple[str, ...]
    shared: tuple[str, ...] = ()


def repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def is_source_file(path: Path) -> bool:
    return path.suffix in SOURCE_EXTENSIONS or path.name in SOURCE_FILENAMES


def has_glob(pattern: str) -> bool:
    return any(char in pattern for char in "*?[")


def path_matches(pattern: str, rel_path: str) -> bool:
    pattern = pattern.strip()
    if not pattern:
        return False
    if has_glob(pattern):
        if pattern.endswith("/"):
            return fnmatch.fnmatch(rel_path, f"{pattern}*")
        return fnmatch.fnmatch(rel_path, pattern)
    if pattern.endswith("/"):
        return rel_path.startswith(pattern)
    return rel_path == pattern or rel_path.startswith(f"{pattern}/")


def first_exclude_reason(rel_path: str, scope_excludes: Iterable[str] = ()) -> str | None:
    for part in Path(rel_path).parts:
        reason = GLOBAL_EXCLUDE_PARTS.get(part)
        if reason:
            return reason
    for pattern, reason in GLOBAL_EXCLUDE_RULES:
        if path_matches(pattern, rel_path):
            return reason
    for pattern in scope_excludes:
        if path_matches(pattern, rel_path):
            return "scope-exclusion"
    return None


def iter_repo_source_files(repo_root: Path = REPO_ROOT) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or not is_source_file(path):
            continue
        files.append(repo_relative(path, repo_root))
    return sorted(files)


def compile_rules(config: Mapping[str, Any], target_type: str) -> list[TargetRule]:
    return [
        TargetRule(
            target_type=target_type,
            target_id=target_id,
            label=payload["label"],
            include=tuple(payload.get("include", [])),
            shared=tuple(payload.get("shared", [])),
        )
        for target_id, payload in config[target_type].items()
    ]


def matching_patterns(patterns: Iterable[str], rel_path: str) -> list[str]:
    return [pattern for pattern in patterns if path_matches(pattern, rel_path)]


def files_matching_patterns(patterns: Iterable[str], files: Iterable[str]) -> list[str]:
    return [path for path in files if matching_patterns(patterns, path)]


def summarize_pattern_status(
    *,
    target_type: str,
    target_id: str,
    match_kind: str,
    patterns: Iterable[str],
    files: Iterable[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    file_list = list(files)
    for pattern in patterns:
        matches = files_matching_patterns([pattern], file_list)
        status = "stale" if not matches else "active"
        if len(matches) >= 100:
            status = "broad"
        out.append(
            {
                "target_type": target_type,
                "target_id": target_id,
                "match_kind": match_kind,
                "pattern": pattern,
                "status": status,
                "match_count": len(matches),
                "sample_matches": matches[:10],
            }
        )
    return out


def likely_unmapped_area(path: str, area_ids: Iterable[str]) -> list[str]:
    ids = set(area_ids)
    checks = {
        "search": ("search",),
        "management": ("management", "manage"),
        "import-export": ("import", "export", "sharing"),
        "config": ("config", "settings"),
        "activity": ("activity", "log"),
        "catalogue": ("catalogue",),
        "docs-build": ("build_docs", "build_search", "rebuild", "generated_reads"),
    }
    lower = path.lower()
    return [area for area, tokens in checks.items() if area not in ids and any(token in lower for token in tokens)]


def likely_unmapped_route(path: str, route_ids: Iterable[str]) -> list[str]:
    ids = set(route_ids)
    checks = {
        "/admin/checks/": ("admin-checks", "checks/", "run_reports", "target_map"),
        "/library/": ("library",),
        "/analysis/": ("analysis",),
        "/docs/": ("docs-viewer-management", "docs_management", "docs-viewer-manage"),
    }
    lower = path.lower()
    return [route for route, tokens in checks.items() if route not in ids and any(token in lower for token in tokens)]


def boundary_flags(
    *,
    families: list[str],
    areas: list[str],
    routes: list[str],
    shared_areas: list[str],
    shared_routes: list[str],
) -> list[str]:
    flags: list[str] = []
    all_areas = sorted(set(areas) | set(shared_areas))
    all_routes = sorted(set(routes) | set(shared_routes))
    if not families:
        flags.append("unclassified-family")
    if len(families) > 1:
        flags.append("multi-family")
    if len(all_areas) > 1:
        flags.append("cross-area")
    if len(all_routes) > 1:
        flags.append("cross-route")
    if "runtime-js" in families and "services" in families:
        flags.append("frontend-backend")
    if routes and "services" in families:
        flags.append("route-service")
    if routes and "config" in families:
        flags.append("route-config")
    if shared_areas or shared_routes:
        flags.append("shared-dependency")
    return flags


def matched_file_payload(path: str, family_rules: list[TargetRule], area_rules: list[TargetRule], route_rules: list[TargetRule]) -> dict[str, Any]:
    families = [rule.target_id for rule in family_rules if matching_patterns(rule.include, path)]
    areas = [rule.target_id for rule in area_rules if matching_patterns(rule.include, path)]
    routes = [rule.target_id for rule in route_rules if matching_patterns(rule.include, path)]
    shared_areas = [rule.target_id for rule in area_rules if matching_patterns(rule.shared, path)]
    shared_routes = [rule.target_id for rule in route_rules if matching_patterns(rule.shared, path)]
    unmapped_areas = likely_unmapped_area(path, areas + shared_areas)
    unmapped_routes = likely_unmapped_route(path, routes + shared_routes)
    flags = boundary_flags(
        families=families,
        areas=areas,
        routes=routes,
        shared_areas=shared_areas,
        shared_routes=shared_routes,
    )
    if unmapped_areas:
        flags.append("likely-unmapped-area")
    if unmapped_routes:
        flags.append("likely-unmapped-route")
    return {
        "path": path,
        "family": families[0] if len(families) == 1 else "_unclassified",
        "families": families,
        "areas": areas,
        "routes": routes,
        "shared_areas": shared_areas,
        "shared_routes": shared_routes,
        "likely_unmapped_areas": unmapped_areas,
        "likely_unmapped_routes": unmapped_routes,
        "boundary_flags": flags,
    }


def resolve_scope(
    config: Mapping[str, Any],
    scope_id: str,
    *,
    source_files: list[str],
    global_source_files: list[str] | None = None,
) -> dict[str, Any]:
    scope = config["scopes"][scope_id]
    include_patterns = scope["include"]
    exclude_patterns = scope.get("exclude", [])
    included = [
        path
        for path in source_files
        if matching_patterns(include_patterns, path) and first_exclude_reason(path, exclude_patterns) is None
    ]
    globally_included = [
        path
        for path in (global_source_files or source_files)
        if first_exclude_reason(path) is None
    ]
    excluded: list[dict[str, str]] = []
    for path in source_files:
        if not matching_patterns(include_patterns, path):
            continue
        reason = first_exclude_reason(path, exclude_patterns)
        if reason:
            excluded.append({"path": path, "reason": reason})

    family_rules = compile_rules(config, "families")
    area_rules = compile_rules(config, "areas")
    route_rules = compile_rules(config, "routes")
    files = [matched_file_payload(path, family_rules, area_rules, route_rules) for path in included]

    family_counts: collections.Counter[str] = collections.Counter()
    area_counts: collections.Counter[str] = collections.Counter()
    route_counts: collections.Counter[str] = collections.Counter()
    shared_dependency_records: list[dict[str, str]] = []
    for file in files:
        for target_id in file["families"] or ["_unclassified"]:
            family_counts[target_id] += 1
        for target_id in file["areas"]:
            area_counts[target_id] += 1
        for target_id in file["routes"]:
            route_counts[target_id] += 1
        for target_id in file["shared_areas"]:
            shared_dependency_records.append({"path": file["path"], "target_type": "areas", "target_id": target_id})
        for target_id in file["shared_routes"]:
            shared_dependency_records.append({"path": file["path"], "target_type": "routes", "target_id": target_id})

    patterns: list[dict[str, Any]] = []
    for target_type, rules in (("families", family_rules), ("areas", area_rules), ("routes", route_rules)):
        for rule in rules:
            patterns.extend(
                summarize_pattern_status(
                    target_type=target_type,
                    target_id=rule.target_id,
                    match_kind="include",
                    patterns=rule.include,
                    files=globally_included,
                )
            )
            patterns.extend(
                summarize_pattern_status(
                    target_type=target_type,
                    target_id=rule.target_id,
                    match_kind="shared",
                    patterns=rule.shared,
                    files=globally_included,
                )
            )

    return {
        "scope_id": scope_id,
        "label": scope["label"],
        "include": list(include_patterns),
        "exclude": list(exclude_patterns),
        "totals": {
            "files": len(files),
            "excluded_files": len(excluded),
            "unclassified_files": sum(1 for file in files if not file["families"]),
            "multi_family_files": sum(1 for file in files if len(file["families"]) > 1),
            "cross_area_files": sum(1 for file in files if len(set(file["areas"]) | set(file["shared_areas"])) > 1),
            "cross_route_files": sum(1 for file in files if len(set(file["routes"]) | set(file["shared_routes"])) > 1),
            "shared_dependency_files": len({record["path"] for record in shared_dependency_records}),
            "stale_patterns": sum(1 for pattern in patterns if pattern["status"] == "stale"),
            "broad_patterns": sum(1 for pattern in patterns if pattern["status"] == "broad"),
            "likely_unmapped_area_files": sum(1 for file in files if file["likely_unmapped_areas"]),
            "likely_unmapped_route_files": sum(1 for file in files if file["likely_unmapped_routes"]),
        },
        "family_counts": dict(sorted(family_counts.items())),
        "area_counts": dict(sorted(area_counts.items())),
        "route_counts": dict(sorted(route_counts.items())),
        "files": files,
        "excluded_files": excluded[:500],
        "shared_dependencies": sorted(shared_dependency_records, key=lambda item: (item["target_type"], item["target_id"], item["path"])),
        "patterns": patterns,
    }


def resolve_target_map(config: Mapping[str, Any], source_files: list[str] | None = None, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    files = source_files if source_files is not None else iter_repo_source_files(repo_root)
    scope_results = [
        resolve_scope(config, scope_id, source_files=files, global_source_files=files)
        for scope_id in config["scopes"]
    ]
    excluded_by_reason: collections.Counter[str] = collections.Counter()
    for path in files:
        reason = first_exclude_reason(path)
        if reason:
            excluded_by_reason[reason] += 1
    return {
        "repo_source_files": len(files),
        "excluded_source_files_by_reason": dict(sorted(excluded_by_reason.items())),
        "scopes": scope_results,
    }


def selected_target_match(file: Mapping[str, Any], families: set[str], areas: set[str], routes: set[str]) -> bool:
    if families and not families.intersection(file["families"]):
        return False
    if areas and not (areas.intersection(file["areas"]) or areas.intersection(file["shared_areas"])):
        return False
    if routes and not (routes.intersection(file["routes"]) or routes.intersection(file["shared_routes"])):
        return False
    return True


def resolve_run_files(
    config: Mapping[str, Any],
    *,
    scope_id: str,
    families: Iterable[str] = (),
    areas: Iterable[str] = (),
    routes: Iterable[str] = (),
    source_files: list[str] | None = None,
    repo_root: Path = REPO_ROOT,
) -> list[dict[str, Any]]:
    files = source_files if source_files is not None else iter_repo_source_files(repo_root)
    scope = resolve_scope(config, scope_id, source_files=files, global_source_files=files)
    selected_families = set(families)
    selected_areas = set(areas)
    selected_routes = set(routes)
    out = [
        file
        for file in scope["files"]
        if selected_target_match(file, selected_families, selected_areas, selected_routes)
    ]
    return out

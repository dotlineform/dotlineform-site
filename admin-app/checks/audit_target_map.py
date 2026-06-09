#!/usr/bin/env python3
"""Audit the draft Admin checks target map against real repo files."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import fnmatch
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("var/admin/checks/target-map-audit")
AUDIT_VERSION = "1"

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
    scope_ids: tuple[str, ...] = ()


def candidate_config() -> dict[str, Any]:
    """Return the draft v1 target rules that Task 2 can promote to config."""

    return {
        "config_id": "admin-checks",
        "version": 1,
        "source": {
            "owner": "admin-app/checks",
            "status": "proposed-by-target-map-audit",
            "producer": "admin-app/checks/audit_target_map.py",
        },
        "scopes": {
            "admin": {
                "label": "Admin",
                "include": ["admin-app/"],
                "exclude": ["admin-app/**/__pycache__/**"],
            },
            "analytics": {
                "label": "Analytics",
                "include": ["analytics-app/"],
                "exclude": ["analytics-app/**/__pycache__/**", "analytics-app/data/canonical/"],
            },
            "docs-viewer": {
                "label": "Docs Viewer",
                "include": ["docs-viewer/", "assets/docs/"],
                "exclude": ["docs-viewer/**/__pycache__/**", "docs-viewer/generated/"],
            },
            "public-site": {
                "label": "Public Site",
                "include": [
                    "_config.yml",
                    "_data/",
                    "_includes/",
                    "_layouts/",
                    "_moments/",
                    "_series/",
                    "_work_details/",
                    "_works/",
                    "_works_print/",
                    "analysis/",
                    "assets/css/",
                    "assets/js/",
                    "catalogue/",
                    "index.md",
                    "library/",
                    "moments/",
                    "recent/",
                    "series/",
                    "work-details/",
                    "works/",
                ],
                "exclude": ["_site/", "assets/data/"],
            },
            "studio": {
                "label": "Studio",
                "include": ["studio/", "data-sharing/"],
                "exclude": ["studio/**/__pycache__/**", "studio/data/generated/", "studio/data/canonical/"],
            },
        },
        "families": {
            "runtime-js": {
                "label": "Runtime JavaScript",
                "include": [
                    "admin-app/app/frontend/js/",
                    "admin-app/ui-catalogue/assets/js/",
                    "analytics-app/app/frontend/js/",
                    "assets/js/",
                    "docs-viewer/runtime/js/",
                    "studio/app/frontend/js/",
                ],
            },
            "services": {
                "label": "Services",
                "include": [
                    "admin-app/app/server/",
                    "analytics-app/app/server/",
                    "data-sharing/data_sharing/",
                    "docs-viewer/services/",
                    "studio/app/server/",
                    "studio/services/",
                    "studio/shared/python/",
                ],
            },
            "build": {
                "label": "Build scripts",
                "include": [
                    "admin-app/checks/",
                    "admin-app/commands/",
                    "bin/",
                    "data-sharing/schemas/",
                    "docs-viewer/bin/",
                    "docs-viewer/build/",
                    "studio/commands/",
                    "studio/checks/",
                ],
            },
            "source-docs": {
                "label": "Source documents",
                "include": [
                    "_moments/",
                    "_series/",
                    "_work_details/",
                    "_works/",
                    "_works_print/",
                    "assets/docs/",
                    "docs-viewer/source/",
                    "admin-app/ui-catalogue/source/",
                    "README.md",
                ],
            },
            "config": {
                "label": "Configuration",
                "include": [
                    "_config.yml",
                    "_data/",
                    "admin-app/app/frontend/config/",
                    "analytics-app/app/frontend/config/",
                    "data-sharing/config/",
                    "docs-viewer/config/",
                    "studio/data/config/",
                    "**/*.yml",
                    "**/*.yaml",
                    "**/*config*.json",
                ],
            },
            "tests": {
                "label": "Tests and smokes",
                "include": [
                    "admin-app/tests/",
                    "analytics-app/tests/",
                    "docs-viewer/tests/",
                    "studio/tests/",
                    "**/tests/",
                ],
            },
            "admin-route": {
                "label": "Admin routes",
                "include": [
                    "admin-app/app/assets/",
                    "admin-app/app/frontend/",
                    "admin-app/app/server/admin_app/admin_*",
                    "admin-app/ui-catalogue/",
                ],
            },
            "public-route": {
                "label": "Public routes",
                "include": [
                    "_includes/",
                    "_layouts/",
                    "analysis/",
                    "assets/css/",
                    "catalogue/",
                    "index.md",
                    "library/",
                    "moments/",
                    "recent/",
                    "series/",
                    "work-details/",
                    "works/",
                    "assets/js/",
                    "docs-viewer/config/routes/docs-viewer-public-routes.json",
                    "docs-viewer/config/defaults/docs-viewer-public-config.json",
                ],
            },
        },
        "areas": {
            "search": {
                "label": "Search",
                "include": [
                    "**/*search*",
                    "assets/js/search/",
                    "catalogue/search/",
                    "docs-viewer/runtime/js/docs-viewer-search*",
                    "docs-viewer/build/*search*",
                    "docs-viewer/tests/**/*search*",
                    "studio/services/catalogue/search/",
                ],
                "shared": ["docs-viewer/runtime/js/docs-viewer-generated-data-runtime.js"],
                "routes": ["/library/", "/analysis/"],
            },
            "management": {
                "label": "Management",
                "include": [
                    "**/*management*",
                    "**/*manage*",
                    "docs-viewer/services/docs_management*",
                    "docs-viewer/tests/smoke/docs_viewer_management*",
                ],
                "shared": [
                    "docs-viewer/runtime/js/docs-viewer-app-context.js",
                    "docs-viewer/runtime/js/docs-viewer-service-context.js",
                ],
                "routes": ["/docs/"],
            },
            "import-export": {
                "label": "Import/export",
                "include": [
                    "**/*import*",
                    "**/*export*",
                    "data-sharing/",
                    "docs-viewer/services/docs_data_sharing/",
                    "docs-viewer/services/documents_data_sharing_adapter.py",
                ],
                "shared": ["docs-viewer/services/docs_management_data_sharing_service.py"],
            },
            "config": {
                "label": "Config",
                "include": [
                    "_config.yml",
                    "**/config/",
                    "**/*config*",
                    "studio/data/config/",
                ],
            },
            "activity": {
                "label": "Activity",
                "include": [
                    "**/*activity*",
                    "admin-app/app/frontend/config/ui-text/admin-activity.json",
                    "admin-app/app/server/admin_app/admin_activity_api.py",
                    "docs-viewer/services/docs_activity.py",
                ],
            },
            "catalogue": {
                "label": "Catalogue",
                "include": [
                    "**/*catalogue*",
                    "catalogue/",
                    "studio/services/catalogue/",
                    "studio/data/config/catalogue/",
                ],
                "shared": ["assets/js/search/"],
            },
            "docs-build": {
                "label": "Docs build",
                "include": [
                    "docs-viewer/build/",
                    "docs-viewer/services/docs_write_rebuild.py",
                    "docs-viewer/services/docs_live_rebuild_watcher.py",
                    "docs-viewer/services/docs_generated_reads.py",
                    "docs-viewer/tests/python/test_build_docs_python.py",
                    "docs-viewer/tests/python/test_build_search_python.py",
                ],
                "shared": ["docs-viewer/config/scopes/", "docs-viewer/source/"],
            },
        },
        "routes": {
            "/admin/checks/": {
                "label": "Admin Checks",
                "path": "/admin/checks/",
                "include": [
                    "admin-app/checks/audit_target_map.py",
                    "admin-app/checks/config/",
                    "admin-app/checks/reports/",
                    "admin-app/checks/run_reports.py",
                    "admin-app/app/frontend/js/admin-checks.js",
                    "admin-app/app/frontend/config/ui-text/admin-checks.json",
                    "admin-app/app/server/admin_app/admin_checks_api.py",
                ],
                "shared": ["admin-app/app/server/admin_app/admin_app_server.py"],
                "areas": ["config"],
            },
            "/admin/risk/": {
                "label": "Admin Risk",
                "path": "/admin/risk/",
                "include": [
                    "admin-app/app/frontend/js/admin-risk.js",
                    "admin-app/app/frontend/config/ui-text/admin-risk.json",
                    "admin-app/app/server/admin_app/admin_risk_api.py",
                    "admin-app/checks/risk_evidence_pack.py",
                    "admin-app/tests/**/*risk*",
                ],
                "shared": ["admin-app/app/server/admin_app/admin_app_server.py"],
                "areas": ["activity"],
            },
            "/library/": {
                "label": "Library",
                "path": "/library/",
                "include": [
                    "library/",
                    "docs-viewer/source/library/",
                    "docs-viewer/config/scopes/docs_scopes.json",
                    "docs-viewer/config/routes/docs-viewer-public-routes.json",
                    "assets/js/search/",
                ],
                "shared": [
                    "docs-viewer/runtime/js/docs-viewer-public.js",
                    "docs-viewer/runtime/js/docs-viewer-route-config.js",
                    "docs-viewer/runtime/js/docs-viewer-search*",
                ],
                "areas": ["search", "catalogue"],
            },
            "/analysis/": {
                "label": "Analysis",
                "path": "/analysis/",
                "include": [
                    "analysis/",
                    "docs-viewer/source/analysis/",
                    "docs-viewer/config/scopes/docs_scopes.json",
                    "docs-viewer/config/routes/docs-viewer-public-routes.json",
                    "assets/js/search/",
                ],
                "shared": [
                    "docs-viewer/runtime/js/docs-viewer-public.js",
                    "docs-viewer/runtime/js/docs-viewer-route-config.js",
                    "docs-viewer/runtime/js/docs-viewer-search*",
                ],
                "areas": ["search"],
            },
            "/docs/": {
                "label": "Docs Viewer Management",
                "path": "/docs/",
                "include": [
                    "docs-viewer/runtime/js/docs-viewer-manage.js",
                    "docs-viewer/runtime/js/docs-viewer-management*",
                    "docs-viewer/services/docs_management*",
                    "docs-viewer/services/docs_viewer_service.py",
                    "docs-viewer/config/routes/docs-viewer-routes.json",
                    "docs-viewer/config/ui-text/manage.json",
                    "docs-viewer/tests/**/*management*",
                    "docs-viewer/tests/smoke/docs_viewer_service_manage.py",
                ],
                "shared": [
                    "docs-viewer/runtime/js/docs-viewer-app-context.js",
                    "docs-viewer/runtime/js/docs-viewer-route-config.js",
                    "docs-viewer/services/docs_management_routes.py",
                ],
                "areas": ["management", "import-export", "docs-build"],
            },
        },
        "reports": {
            "files": {
                "label": "Files",
                "script": "admin-app/checks/reports/files.py",
                "description": "File count, line count, and byte size evidence.",
            }
        },
    }


def repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


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


def iter_repo_source_files(repo_root: Path) -> list[str]:
    files: list[str] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or not is_source_file(path):
            continue
        files.append(repo_relative(path, repo_root))
    return sorted(files)


def scope_definitions(config: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    scopes = dict(config["scopes"])
    all_include: list[str] = []
    all_exclude: list[str] = []
    for scope in scopes.values():
        all_include.extend(scope["include"])
        all_exclude.extend(scope.get("exclude", []))
    scopes["all"] = {
        "label": "All",
        "include": sorted(dict.fromkeys(all_include)),
        "exclude": sorted(dict.fromkeys(all_exclude)),
    }
    return scopes


def compile_rules(config: Mapping[str, Any], target_type: str) -> list[TargetRule]:
    out: list[TargetRule] = []
    for target_id, payload in config[target_type].items():
        out.append(
            TargetRule(
                target_type=target_type,
                target_id=target_id,
                label=payload["label"],
                include=tuple(payload.get("include", [])),
                shared=tuple(payload.get("shared", [])),
                scope_ids=tuple(payload.get("scope_ids", [])),
            )
        )
    return out


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
        "/admin/risk/": ("admin-risk", "risk"),
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


def audit_scope(
    scope_id: str,
    scope: Mapping[str, Any],
    *,
    source_files: list[str],
    family_rules: list[TargetRule],
    area_rules: list[TargetRule],
    route_rules: list[TargetRule],
) -> dict[str, Any]:
    include_patterns = scope["include"]
    exclude_patterns = scope.get("exclude", [])
    included = [
        path
        for path in source_files
        if matching_patterns(include_patterns, path) and first_exclude_reason(path, exclude_patterns) is None
    ]
    globally_included = [path for path in source_files if first_exclude_reason(path) is None]
    excluded: list[dict[str, str]] = []
    for path in source_files:
        if not matching_patterns(include_patterns, path):
            continue
        reason = first_exclude_reason(path, exclude_patterns)
        if reason:
            excluded.append({"path": path, "reason": reason})

    files: list[dict[str, Any]] = []
    family_counts: collections.Counter[str] = collections.Counter()
    area_counts: collections.Counter[str] = collections.Counter()
    route_counts: collections.Counter[str] = collections.Counter()
    shared_dependency_records: list[dict[str, str]] = []

    for path in included:
        families = [rule.target_id for rule in family_rules if matching_patterns(rule.include, path)]
        areas = [rule.target_id for rule in area_rules if matching_patterns(rule.include, path)]
        routes = [rule.target_id for rule in route_rules if matching_patterns(rule.include, path)]
        shared_areas = [rule.target_id for rule in area_rules if matching_patterns(rule.shared, path)]
        shared_routes = [rule.target_id for rule in route_rules if matching_patterns(rule.shared, path)]

        for target_id in families or ["_unclassified"]:
            family_counts[target_id] += 1
        for target_id in areas:
            area_counts[target_id] += 1
        for target_id in routes:
            route_counts[target_id] += 1
        for target_id in shared_areas:
            shared_dependency_records.append({"path": path, "target_type": "areas", "target_id": target_id})
        for target_id in shared_routes:
            shared_dependency_records.append({"path": path, "target_type": "routes", "target_id": target_id})

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

        files.append(
            {
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
        )

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


def build_audit(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    config = candidate_config()
    source_files = iter_repo_source_files(repo_root)
    scopes = scope_definitions(config)
    family_rules = compile_rules(config, "families")
    area_rules = compile_rules(config, "areas")
    route_rules = compile_rules(config, "routes")
    scope_results = [
        audit_scope(
            scope_id,
            scope,
            source_files=source_files,
            family_rules=family_rules,
            area_rules=area_rules,
            route_rules=route_rules,
        )
        for scope_id, scope in scopes.items()
    ]
    total_excluded_by_reason: collections.Counter[str] = collections.Counter()
    for path in source_files:
        reason = first_exclude_reason(path)
        if reason:
            total_excluded_by_reason[reason] += 1

    return {
        "schema_version": "admin_checks_target_map_audit_v1",
        "audit_version": AUDIT_VERSION,
        "created_at": utc_timestamp(),
        "producer": "admin-app/checks/audit_target_map.py",
        "repo_root": repo_relative(repo_root, repo_root),
        "summary": {
            "repo_source_files": len(source_files),
            "excluded_source_files_by_reason": dict(sorted(total_excluded_by_reason.items())),
            "scopes": {
                result["scope_id"]: result["totals"]
                for result in scope_results
            },
        },
        "proposed_admin_checks_config": config,
        "scopes": scope_results,
    }


def table_row(cells: Iterable[object]) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def top_files(scope: Mapping[str, Any], flag: str, limit: int = 12) -> list[Mapping[str, Any]]:
    return [file for file in scope["files"] if flag in file["boundary_flags"]][:limit]


def render_markdown(audit: Mapping[str, Any]) -> str:
    lines: list[str] = [
        "# Target Map Audit",
        "",
        f"- created: {audit['created_at']}",
        f"- producer: `{audit['producer']}`",
        f"- repo source files scanned: {audit['summary']['repo_source_files']}",
        "",
        "## Scope Totals",
        "",
        table_row(
            [
                "scope",
                "files",
                "excluded",
                "unclassified",
                "multi-family",
                "cross-area",
                "cross-route",
                "shared deps",
                "stale patterns",
            ]
        ),
        table_row(["---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"]),
    ]
    for scope in audit["scopes"]:
        totals = scope["totals"]
        lines.append(
            table_row(
                [
                    f"`{scope['scope_id']}`",
                    totals["files"],
                    totals["excluded_files"],
                    totals["unclassified_files"],
                    totals["multi_family_files"],
                    totals["cross_area_files"],
                    totals["cross_route_files"],
                    totals["shared_dependency_files"],
                    totals["stale_patterns"],
                ]
            )
        )

    lines.extend(["", "## Proposed Target Rules", ""])
    config = audit["proposed_admin_checks_config"]
    lines.extend(
        [
            f"- scopes: {', '.join(f'`{key}`' for key in sorted(scope_definitions(config)))}",
            f"- families: {', '.join(f'`{key}`' for key in sorted(config['families']))}",
            f"- areas: {', '.join(f'`{key}`' for key in sorted(config['areas']))}",
            f"- routes: {', '.join(f'`{key}`' for key in sorted(config['routes']))}",
            "",
            "## Findings For Review",
            "",
        ]
    )

    for scope in audit["scopes"]:
        totals = scope["totals"]
        lines.extend([f"### {scope['label']} (`{scope['scope_id']}`)", ""])
        lines.append(
            "Review priority: "
            f"{totals['unclassified_files']} unclassified, "
            f"{totals['multi_family_files']} multi-family, "
            f"{totals['likely_unmapped_area_files']} likely area gaps, "
            f"{totals['likely_unmapped_route_files']} likely route gaps."
        )
        lines.append("")
        for heading, flag in (
            ("Unclassified files", "unclassified-family"),
            ("Multi-family files", "multi-family"),
            ("Cross-area files", "cross-area"),
            ("Cross-route files", "cross-route"),
            ("Likely unmapped route files", "likely-unmapped-route"),
        ):
            rows = top_files(scope, flag)
            if not rows:
                continue
            lines.extend([f"#### {heading}", "", table_row(["path", "families", "areas", "routes", "flags"]), table_row(["---", "---", "---", "---", "---"])])
            for row in rows:
                lines.append(
                    table_row(
                        [
                            f"`{row['path']}`",
                            ", ".join(row["families"]) or "_unclassified",
                            ", ".join(sorted(set(row["areas"]) | set(row["shared_areas"]))) or "-",
                            ", ".join(sorted(set(row["routes"]) | set(row["shared_routes"]))) or "-",
                            ", ".join(row["boundary_flags"]),
                        ]
                    )
                )
            lines.append("")

        stale = [pattern for pattern in scope["patterns"] if pattern["status"] == "stale"][:15]
        if stale:
            lines.extend(["#### Stale Patterns", "", table_row(["target", "kind", "pattern"]), table_row(["---", "---", "---"])])
            for pattern in stale:
                lines.append(
                    table_row(
                        [
                            f"`{pattern['target_type']}.{pattern['target_id']}`",
                            pattern["match_kind"],
                            f"`{pattern['pattern']}`",
                        ]
                    )
                )
            lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Findings are mapping data, not automatic pass/fail policy.",
            "- `_unclassified` means no draft family rule matched the file.",
            "- Shared dependencies are explicit matches from target `shared` rules.",
            "- Stale patterns are expected during Batch 1 where future checks files are proposed but not implemented yet.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(audit: Mapping[str, Any], markdown: str, output_root: Path, repo_root: Path) -> tuple[Path, Path]:
    out_dir = repo_root / output_root
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "target-map.json"
    md_path = out_dir / "target-map.md"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the draft Admin checks target map.")
    parser.add_argument("--write", action="store_true", help="Write target-map artifacts under var/admin/checks/target-map-audit/.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT.as_posix(),
        help="Project-relative output directory for --write.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = build_audit(REPO_ROOT)
    markdown = render_markdown(audit)
    if args.write:
        json_path, md_path = write_outputs(audit, markdown, Path(args.output_root), REPO_ROOT)
        print(f"Wrote {repo_relative(json_path)}")
        print(f"Wrote {repo_relative(md_path)}")
        return 0
    if args.json:
        print(json.dumps(audit, indent=2, sort_keys=True))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

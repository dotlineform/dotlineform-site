#!/usr/bin/env python3
"""Produce target-map boundary evidence for Admin checks."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


CHECKS_ROOT = Path(__file__).resolve().parents[1]
if str(CHECKS_ROOT) not in sys.path:
    sys.path.insert(0, str(CHECKS_ROOT))

from admin_checks_config import DEFAULT_CONFIG_PATH, ChecksConfigError, load_checks_config, validate_path_pattern  # noqa: E402
from target_map_resolver import (  # noqa: E402
    REPO_ROOT,
    iter_repo_source_files,
    repo_relative,
    resolve_scope,
    selected_target_match,
)


REPORT_SCHEMA_VERSION = "admin_checks_target_map_report_v1"
RUNS_ROOT = "var/admin/checks/"
REVIEW_FLAGS = (
    "unclassified-family",
    "multi-family",
    "cross-area",
    "cross-route",
    "frontend-backend",
    "route-service",
    "route-config",
    "shared-dependency",
    "likely-unmapped-area",
    "likely-unmapped-route",
)


class TargetMapReportError(RuntimeError):
    """Raised when the target-map report cannot be produced."""


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TargetMapReportError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise TargetMapReportError(f"{label} must be a JSON object")
    return payload


def safe_repo_path(path_text: str, *, label: str, repo_root: Path = REPO_ROOT) -> Path:
    validate_path_pattern(path_text, label)
    return repo_root / path_text


def safe_run_artifact_path(path_text: str, *, label: str, repo_root: Path = REPO_ROOT) -> Path:
    validate_path_pattern(path_text, label)
    if path_text != RUNS_ROOT.rstrip("/") and not path_text.startswith(RUNS_ROOT):
        raise TargetMapReportError(f"{label} must be under {RUNS_ROOT}")
    return repo_root / path_text


def find_report_plan(manifest: Mapping[str, Any], report_id: str) -> Mapping[str, Any]:
    reports = manifest.get("reports")
    if not isinstance(reports, list):
        raise TargetMapReportError("run manifest reports must be a list")
    for report in reports:
        if isinstance(report, dict) and report.get("report_id") == report_id:
            return report
    raise TargetMapReportError(f"run manifest does not include report {report_id}")


def as_int_option(options: Mapping[str, Any], key: str) -> int:
    value = options.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TargetMapReportError(f"{key} option must be an integer")
    return value


def target_ids(targets: Mapping[str, Any], key: str) -> list[str]:
    values = targets.get(key, [])
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise TargetMapReportError(f"run manifest targets.{key} must be a list of strings")
    return values


def selected_text(values: Iterable[str]) -> str:
    items = list(values)
    return ", ".join(f"`{item}`" for item in items) if items else "_all_"


def short_file_name(path: str) -> str:
    return Path(path).name


def truncate_text(value: object, width: int) -> str:
    text = str(value)
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return f"{text[: width - 3]}..."


def padded_cell(value: object, width: int, align: str) -> str:
    text = truncate_text(value, width)
    if align == "right":
        return text.rjust(width)
    return text.ljust(width)


def render_text_columns(
    lines: list[str],
    columns: list[tuple[str, int, str]],
    rows: Iterable[Iterable[object]],
) -> None:
    lines.append("```text")
    lines.append("  ".join(padded_cell(header, width, align) for header, width, align in columns).rstrip())
    lines.append("  ".join("-" * width for _header, width, _align in columns).rstrip())
    for row in rows:
        lines.append(
            "  ".join(
                padded_cell(value, width, align)
                for value, (_header, width, align) in zip(row, columns, strict=True)
            ).rstrip()
        )
    lines.append("```")


def all_areas(file: Mapping[str, Any]) -> list[str]:
    return sorted(set(file["areas"]) | set(file["shared_areas"]))


def all_routes(file: Mapping[str, Any]) -> list[str]:
    return sorted(set(file["routes"]) | set(file["shared_routes"]))


def selected_files(
    scope_files: Iterable[Mapping[str, Any]],
    *,
    families: Iterable[str],
    areas: Iterable[str],
    routes: Iterable[str],
) -> list[dict[str, Any]]:
    family_ids = set(families)
    area_ids = set(areas)
    route_ids = set(routes)
    return [
        dict(file)
        for file in scope_files
        if selected_target_match(file, family_ids, area_ids, route_ids)
    ]


def count_targets(files: Iterable[Mapping[str, Any]], key: str, shared_key: str | None = None) -> dict[str, int]:
    counts: collections.Counter[str] = collections.Counter()
    for file in files:
        values = set(file[key])
        if shared_key:
            values.update(file[shared_key])
        if key == "families" and not values:
            values.add("_unclassified")
        counts.update(values)
    return dict(sorted(counts.items()))


def report_totals(files: list[Mapping[str, Any]], patterns: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "files": len(files),
        "unclassified_files": sum(1 for file in files if not file["families"]),
        "multi_family_files": sum(1 for file in files if len(file["families"]) > 1),
        "cross_area_files": sum(1 for file in files if len(all_areas(file)) > 1),
        "cross_route_files": sum(1 for file in files if len(all_routes(file)) > 1),
        "shared_dependency_files": sum(1 for file in files if "shared-dependency" in file["boundary_flags"]),
        "stale_patterns": sum(1 for pattern in patterns if pattern["status"] == "stale"),
        "broad_patterns": sum(1 for pattern in patterns if pattern["status"] == "broad"),
        "likely_unmapped_area_files": sum(1 for file in files if file["likely_unmapped_areas"]),
        "likely_unmapped_route_files": sum(1 for file in files if file["likely_unmapped_routes"]),
    }


def grouped_shared_dependencies(files: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for file in files:
        shared_areas = list(file["shared_areas"])
        shared_routes = list(file["shared_routes"])
        if not shared_areas and not shared_routes:
            continue
        rows.append(
            {
                "path": file["path"],
                "shared_areas": shared_areas,
                "shared_routes": shared_routes,
                "target_count": len(set(shared_areas) | set(shared_routes)),
            }
        )
    return sorted(rows, key=lambda row: (-int(row["target_count"]), row["path"]))


def review_files(files: Iterable[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for flag in REVIEW_FLAGS:
        rows = [dict(file) for file in files if flag in file["boundary_flags"]]
        if rows:
            grouped[flag] = sorted(rows, key=lambda row: row["path"])
    return grouped


def build_report(
    *,
    config: Mapping[str, Any],
    manifest: Mapping[str, Any],
    report_id: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if report_id != "target-map":
        raise TargetMapReportError(f"target_map.py cannot produce report {report_id}")
    report_plan = find_report_plan(manifest, report_id)
    options = report_plan.get("options", {})
    if not isinstance(options, dict):
        raise TargetMapReportError("target-map report options must be an object")
    limit = as_int_option(options, "limit")
    pattern_limit = as_int_option(options, "pattern_limit")

    targets = manifest.get("targets")
    if not isinstance(targets, dict):
        raise TargetMapReportError("run manifest targets must be an object")
    scope = targets.get("scope")
    if not isinstance(scope, str) or not scope:
        raise TargetMapReportError("run manifest targets.scope must be a string")
    families = target_ids(targets, "families")
    areas = target_ids(targets, "areas")
    routes = target_ids(targets, "routes")

    source_files = iter_repo_source_files(repo_root)
    resolved_scope = resolve_scope(config, scope, source_files=source_files, global_source_files=source_files)
    files = selected_files(resolved_scope["files"], families=families, areas=areas, routes=routes)
    patterns = list(resolved_scope["patterns"])
    totals = report_totals(files, patterns)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "created_at": utc_timestamp(),
        "report_id": report_id,
        "producer": "admin-app/checks/reports/target_map.py",
        "run_id": manifest.get("run_id"),
        "targets": {
            "scope": scope,
            "families": families,
            "areas": areas,
            "routes": routes,
        },
        "options": {
            "limit": limit,
            "pattern_limit": pattern_limit,
        },
        "scope": {
            "scope_id": resolved_scope["scope_id"],
            "label": resolved_scope["label"],
            "include": resolved_scope["include"],
            "exclude": resolved_scope["exclude"],
            "totals": resolved_scope["totals"],
        },
        "totals": totals,
        "target_counts": {
            "families": count_targets(files, "families"),
            "areas": count_targets(files, "areas", "shared_areas"),
            "routes": count_targets(files, "routes", "shared_routes"),
        },
        "files": files,
        "shared_dependencies": grouped_shared_dependencies(files),
        "review_files": review_files(files),
        "patterns": patterns,
    }


def render_file_findings(lines: list[str], rows: list[Mapping[str, Any]], limit: int) -> None:
    shown = rows[:limit]
    render_text_columns(
        lines,
        [
            ("File", 34, "left"),
            ("Families", 24, "left"),
            ("Areas", 28, "left"),
            ("Routes", 26, "left"),
        ],
        [
            [
                short_file_name(str(row["path"])),
                ", ".join(row["families"]) or "_unclassified",
                ", ".join(all_areas(row)) or "-",
                ", ".join(all_routes(row)) or "-",
            ]
            for row in shown
        ],
    )
    if len(rows) > len(shown):
        lines.extend(["", f"_Showing {len(shown)} of {len(rows)} files._"])


def render_markdown(report: Mapping[str, Any]) -> str:
    targets = report["targets"]
    options = report["options"]
    totals = report["totals"]
    limit = int(options["limit"])
    pattern_limit = int(options["pattern_limit"])
    lines = [
        "# Target Map Report",
        "",
        f"- report: `{report['report_id']}`",
        f"- run: `{report['run_id']}`",
        f"- scope: `{targets['scope']}`",
        f"- families: {selected_text(targets['families'])}",
        f"- areas: {selected_text(targets['areas'])}",
        f"- routes: {selected_text(targets['routes'])}",
        f"- files: {totals['files']}",
        f"- unclassified files: {totals['unclassified_files']}",
        f"- multi-family files: {totals['multi_family_files']}",
        f"- cross-area files: {totals['cross_area_files']}",
        f"- cross-route files: {totals['cross_route_files']}",
        f"- shared dependency files: {totals['shared_dependency_files']}",
        f"- stale patterns: {totals['stale_patterns']}",
        f"- broad patterns: {totals['broad_patterns']}",
        "",
        "## Review Questions",
        "",
        f"- Are any in-scope code files unclassified? {totals['unclassified_files']}",
        f"- Do any files cross multiple families, areas, or routes? {totals['multi_family_files'] + totals['cross_area_files'] + totals['cross_route_files']}",
        f"- Which files are intentional shared dependencies? {totals['shared_dependency_files']}",
        f"- Which configured target patterns need cleanup? {totals['stale_patterns'] + totals['broad_patterns']}",
        "",
        "## Target Counts",
        "",
    ]
    for target_type, counts in report["target_counts"].items():
        rows = [[key, value] for key, value in counts.items()]
        lines.extend([f"### {target_type}", ""])
        render_text_columns(lines, [("Target", 34, "left"), ("Files", 5, "right")], rows or [["-", 0]])
        lines.append("")

    shared_rows = report["shared_dependencies"][:limit]
    if shared_rows:
        lines.extend(["## Shared Dependencies", ""])
        render_text_columns(
            lines,
            [
                ("File", 34, "left"),
                ("Areas", 28, "left"),
                ("Routes", 26, "left"),
                ("Targets", 7, "right"),
            ],
            [
                [
                    short_file_name(str(row["path"])),
                    ", ".join(row["shared_areas"]) or "-",
                    ", ".join(row["shared_routes"]) or "-",
                    row["target_count"],
                ]
                for row in shared_rows
            ],
        )
        if len(report["shared_dependencies"]) > len(shared_rows):
            lines.extend(["", f"_Showing {len(shared_rows)} of {len(report['shared_dependencies'])} shared dependency files._"])
        lines.append("")

    review_files_by_flag = report["review_files"]
    if review_files_by_flag:
        lines.extend(["## Boundary Findings", ""])
        for flag in REVIEW_FLAGS:
            rows = review_files_by_flag.get(flag, [])
            if not rows:
                continue
            lines.extend([f"### {flag}", ""])
            render_file_findings(lines, rows, limit)
            lines.append("")

    review_patterns = [pattern for pattern in report["patterns"] if pattern["status"] in {"stale", "broad"}]
    if review_patterns:
        lines.extend(["## Pattern Findings", ""])
        render_text_columns(
            lines,
            [
                ("Status", 8, "left"),
                ("Target", 32, "left"),
                ("Kind", 10, "left"),
                ("Matches", 7, "right"),
                ("Pattern", 52, "left"),
            ],
            [
                [
                    pattern["status"],
                    f"{pattern['target_type']}.{pattern['target_id']}",
                    pattern["match_kind"],
                    pattern["match_count"],
                    pattern["pattern"],
                ]
                for pattern in review_patterns[:pattern_limit]
            ],
        )
        if len(review_patterns) > pattern_limit:
            lines.extend(["", f"_Showing {pattern_limit} of {len(review_patterns)} pattern findings._"])
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Findings are target-map evidence, not automatic pass/fail policy.",
            "- `_unclassified` means no configured family rule matched the file.",
            "- Shared dependencies are explicit matches from target `shared` rules.",
            "- Stale patterns match no current source files; broad patterns match unusually many source files.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: Mapping[str, Any], markdown: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce the Admin checks target-map report.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH.as_posix(), help="Repo-relative Admin checks config path.")
    parser.add_argument("--run-manifest", required=True, help="Repo-relative run manifest path.")
    parser.add_argument("--report-id", required=True, help="Report id to produce. Must be target-map.")
    parser.add_argument("--output-dir", required=True, help="Repo-relative output directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config_path = Path(args.config)
        safe_repo_path(config_path.as_posix(), label="--config")
        manifest_path = safe_run_artifact_path(args.run_manifest, label="--run-manifest")
        output_dir = safe_run_artifact_path(args.output_dir, label="--output-dir")
        config = load_checks_config(config_path, REPO_ROOT)
        manifest = read_json_object(manifest_path, "run manifest")
        report = build_report(config=config, manifest=manifest, report_id=args.report_id, repo_root=REPO_ROOT)
        markdown = render_markdown(report)
        json_path, md_path = write_outputs(report, markdown, output_dir)
    except (ChecksConfigError, TargetMapReportError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {repo_relative(json_path)}")
    print(f"Wrote {repo_relative(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

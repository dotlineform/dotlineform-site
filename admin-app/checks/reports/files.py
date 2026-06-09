#!/usr/bin/env python3
"""Produce file count, line count, and byte-size evidence for Admin checks."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


CHECKS_ROOT = Path(__file__).resolve().parents[1]
if str(CHECKS_ROOT) not in sys.path:
    sys.path.insert(0, str(CHECKS_ROOT))

from admin_checks_config import DEFAULT_CONFIG_PATH, ChecksConfigError, load_checks_config, validate_path_pattern  # noqa: E402
from target_map_resolver import REPO_ROOT, iter_repo_source_files, repo_relative, resolve_run_files  # noqa: E402


REPORT_SCHEMA_VERSION = "admin_checks_files_report_v1"
VALID_SORTS = {"lines_desc", "bytes_desc", "path_asc"}
RUNS_ROOT = "var/admin/checks/"


class FilesReportError(RuntimeError):
    """Raised when the files report cannot be produced."""


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json_object(path: Path, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FilesReportError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise FilesReportError(f"{label} must be a JSON object")
    return payload


def safe_repo_path(path_text: str, *, label: str, repo_root: Path = REPO_ROOT) -> Path:
    validate_path_pattern(path_text, label)
    return repo_root / path_text


def safe_run_artifact_path(path_text: str, *, label: str, repo_root: Path = REPO_ROOT) -> Path:
    validate_path_pattern(path_text, label)
    if path_text != RUNS_ROOT.rstrip("/") and not path_text.startswith(RUNS_ROOT):
        raise FilesReportError(f"{label} must be under {RUNS_ROOT}")
    return repo_root / path_text


def find_report_plan(manifest: Mapping[str, Any], report_id: str) -> Mapping[str, Any]:
    reports = manifest.get("reports")
    if not isinstance(reports, list):
        raise FilesReportError("run manifest reports must be a list")
    for report in reports:
        if isinstance(report, dict) and report.get("report_id") == report_id:
            return report
    raise FilesReportError(f"run manifest does not include report {report_id}")


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        return sum(1 for _line in handle)


def target_match_kind(file: Mapping[str, Any], selected_areas: set[str], selected_routes: set[str]) -> str:
    if not file["families"]:
        return "_unclassified"
    shared_area_match = bool(selected_areas.intersection(file["shared_areas"]))
    shared_route_match = bool(selected_routes.intersection(file["shared_routes"]))
    direct_area_match = bool(selected_areas.intersection(file["areas"]))
    direct_route_match = bool(selected_routes.intersection(file["routes"]))
    if (shared_area_match and not direct_area_match) or (shared_route_match and not direct_route_match):
        return "shared"
    return "direct"


def measure_files(
    resolved_files: Iterable[Mapping[str, Any]],
    *,
    repo_root: Path,
    selected_areas: Iterable[str],
    selected_routes: Iterable[str],
) -> list[dict[str, Any]]:
    area_ids = set(selected_areas)
    route_ids = set(selected_routes)
    rows: list[dict[str, Any]] = []
    for file in resolved_files:
        path_text = file["path"]
        path = repo_root / path_text
        lines = count_lines(path)
        bytes_size = path.stat().st_size
        rows.append(
            {
                "path": path_text,
                "lines": lines,
                "bytes": bytes_size,
                "family": file["family"],
                "families": file["families"],
                "areas": file["areas"],
                "routes": file["routes"],
                "shared_areas": file["shared_areas"],
                "shared_routes": file["shared_routes"],
                "target_match": target_match_kind(file, area_ids, route_ids),
            }
        )
    return rows


def sort_rows(rows: list[dict[str, Any]], sort: str) -> list[dict[str, Any]]:
    if sort == "lines_desc":
        return sorted(rows, key=lambda row: (-int(row["lines"]), str(row["path"])))
    if sort == "bytes_desc":
        return sorted(rows, key=lambda row: (-int(row["bytes"]), str(row["path"])))
    if sort == "path_asc":
        return sorted(rows, key=lambda row: str(row["path"]))
    raise FilesReportError(f"unsupported sort option: {sort}")


def totals(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "files": len(rows),
        "lines": sum(int(row["lines"]) for row in rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
    }


def as_int_option(options: Mapping[str, Any], key: str) -> int:
    value = options.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise FilesReportError(f"{key} option must be an integer")
    return value


def as_string_option(options: Mapping[str, Any], key: str) -> str:
    value = options.get(key)
    if not isinstance(value, str):
        raise FilesReportError(f"{key} option must be a string")
    return value


def build_report(
    *,
    config: Mapping[str, Any],
    manifest: Mapping[str, Any],
    report_id: str,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    if report_id != "files":
        raise FilesReportError(f"files.py cannot produce report {report_id}")
    report_plan = find_report_plan(manifest, report_id)
    options = report_plan.get("options", {})
    if not isinstance(options, dict):
        raise FilesReportError("files report options must be an object")
    limit = as_int_option(options, "limit")
    sort = as_string_option(options, "sort")
    if sort not in VALID_SORTS:
        raise FilesReportError(f"unsupported sort option: {sort}")

    targets = manifest.get("targets")
    if not isinstance(targets, dict):
        raise FilesReportError("run manifest targets must be an object")
    scope = targets.get("scope")
    if not isinstance(scope, str) or not scope:
        raise FilesReportError("run manifest targets.scope must be a string")
    families = targets.get("families", [])
    areas = targets.get("areas", [])
    routes = targets.get("routes", [])
    if not isinstance(families, list) or not isinstance(areas, list) or not isinstance(routes, list):
        raise FilesReportError("run manifest target filters must be lists")

    source_files = iter_repo_source_files(repo_root)
    resolved = resolve_run_files(
        config,
        scope_id=scope,
        families=families,
        areas=areas,
        routes=routes,
        source_files=source_files,
        repo_root=repo_root,
    )
    rows = sort_rows(
        measure_files(
            resolved,
            repo_root=repo_root,
            selected_areas=areas,
            selected_routes=routes,
        ),
        sort,
    )
    report_totals = totals(rows)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "created_at": utc_timestamp(),
        "report_id": report_id,
        "producer": "admin-app/checks/reports/files.py",
        "run_id": manifest.get("run_id"),
        "targets": {
            "scope": scope,
            "families": families,
            "areas": areas,
            "routes": routes,
        },
        "options": {
            "limit": limit,
            "sort": sort,
        },
        "totals": report_totals,
        "files": rows,
    }


def byte_label(value: int) -> str:
    if value < 1024:
        return f"{value}B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f}K"
    return f"{value / (1024 * 1024):.1f}M"


def selected_text(values: Iterable[str]) -> str:
    items = list(values)
    return ", ".join(f"`{item}`" for item in items) if items else "_all_"


def table_row(cells: Iterable[object]) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def render_markdown(report: Mapping[str, Any]) -> str:
    targets = report["targets"]
    options = report["options"]
    report_totals = report["totals"]
    files = report["files"]
    limit = int(options["limit"])
    shown_files = files[:limit]
    lines = [
        "# Files Report",
        "",
        f"- report: `{report['report_id']}`",
        f"- run: `{report['run_id']}`",
        f"- scope: `{targets['scope']}`",
        f"- families: {selected_text(targets['families'])}",
        f"- areas: {selected_text(targets['areas'])}",
        f"- routes: {selected_text(targets['routes'])}",
        f"- files: {report_totals['files']}",
        f"- total lines: {report_totals['lines']}",
        f"- total bytes: {report_totals['bytes']} ({byte_label(int(report_totals['bytes']))})",
        "",
        "## Largest Files",
        "",
        table_row(["lines", "bytes", "family", "target", "path"]),
        table_row(["---:", "---:", "---", "---", "---"]),
    ]
    for row in shown_files:
        lines.append(
            table_row(
                [
                    row["lines"],
                    row["bytes"],
                    row["family"],
                    row["target_match"],
                    f"`{row['path']}`",
                ]
            )
        )
    if len(files) > len(shown_files):
        lines.extend(["", f"_Showing {len(shown_files)} of {len(files)} files._"])
    lines.append("")
    return "\n".join(lines)


def write_outputs(report: Mapping[str, Any], markdown: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "report.json"
    md_path = output_dir / "report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce the Admin checks files report.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH.as_posix(), help="Repo-relative Admin checks config path.")
    parser.add_argument("--run-manifest", required=True, help="Repo-relative run manifest path.")
    parser.add_argument("--report-id", required=True, help="Report id to produce. Must be files.")
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
    except (ChecksConfigError, FilesReportError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {repo_relative(json_path)}")
    print(f"Wrote {repo_relative(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

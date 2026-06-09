#!/usr/bin/env python3
"""Audit the Admin checks target map against real repo files."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Iterable, Mapping

from admin_checks_config import DEFAULT_CONFIG_PATH, load_checks_config
from target_map_resolver import REPO_ROOT, repo_relative, resolve_target_map


DEFAULT_OUTPUT_ROOT = Path("var/admin/checks/target-map-audit")
AUDIT_VERSION = "2"


def utc_timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def build_audit(config_path: Path = DEFAULT_CONFIG_PATH, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    config = load_checks_config(config_path, repo_root)
    resolved = resolve_target_map(config, repo_root=repo_root)
    scope_results = resolved["scopes"]
    return {
        "schema_version": "admin_checks_target_map_audit_v1",
        "audit_version": AUDIT_VERSION,
        "created_at": utc_timestamp(),
        "producer": "admin-app/checks/audit_target_map.py",
        "config_path": config_path.as_posix(),
        "repo_root": repo_relative(repo_root, repo_root),
        "summary": {
            "repo_source_files": resolved["repo_source_files"],
            "excluded_source_files_by_reason": resolved["excluded_source_files_by_reason"],
            "scopes": {
                result["scope_id"]: result["totals"]
                for result in scope_results
            },
        },
        "config_summary": {
            "config_id": config["config_id"],
            "version": config["version"],
            "scopes": sorted(config["scopes"]),
            "families": sorted(config["families"]),
            "areas": sorted(config["areas"]),
            "routes": sorted(config["routes"]),
            "reports": sorted(config["reports"]),
        },
        "scopes": scope_results,
    }


def table_row(cells: Iterable[object]) -> str:
    return "| " + " | ".join(str(cell) for cell in cells) + " |"


def top_files(scope: Mapping[str, object], flag: str, limit: int = 12) -> list[Mapping[str, object]]:
    files = scope["files"]
    if not isinstance(files, list):
        return []
    return [file for file in files if flag in file["boundary_flags"]][:limit]


def render_markdown(audit: Mapping[str, object]) -> str:
    summary = audit["summary"]
    if not isinstance(summary, dict):
        raise TypeError("audit summary must be a mapping")
    config_summary = audit["config_summary"]
    if not isinstance(config_summary, dict):
        raise TypeError("audit config_summary must be a mapping")

    lines: list[str] = [
        "# Target Map Audit",
        "",
        f"- created: {audit['created_at']}",
        f"- producer: `{audit['producer']}`",
        f"- config: `{audit['config_path']}`",
        f"- repo source files scanned: {summary['repo_source_files']}",
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
    scopes = audit["scopes"]
    if not isinstance(scopes, list):
        raise TypeError("audit scopes must be a list")
    for scope in scopes:
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

    lines.extend(["", "## Config Targets", ""])
    lines.extend(
        [
            f"- config: `{config_summary['config_id']}` v{config_summary['version']}",
            f"- scopes: {', '.join(f'`{key}`' for key in config_summary['scopes'])}",
            f"- families: {', '.join(f'`{key}`' for key in config_summary['families'])}",
            f"- areas: {', '.join(f'`{key}`' for key in config_summary['areas'])}",
            f"- routes: {', '.join(f'`{key}`' for key in config_summary['routes'])}",
            f"- reports: {', '.join(f'`{key}`' for key in config_summary['reports'])}",
            "",
            "## Findings For Review",
            "",
        ]
    )

    for scope in scopes:
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
            lines.extend(
                [
                    f"#### {heading}",
                    "",
                    table_row(["path", "families", "areas", "routes", "flags"]),
                    table_row(["---", "---", "---", "---", "---"]),
                ]
            )
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
            "- `_unclassified` means no configured family rule matched the file.",
            "- Shared dependencies are explicit matches from target `shared` rules.",
            "- Stale patterns indicate configured patterns that match no current source files.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(audit: Mapping[str, object], markdown: str, output_root: Path, repo_root: Path) -> tuple[Path, Path]:
    out_dir = repo_root / output_root
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "target-map.json"
    md_path = out_dir / "target-map.md"
    json_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Admin checks target map.")
    parser.add_argument("--write", action="store_true", help="Write target-map artifacts under var/admin/checks/target-map-audit/.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown.")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH.as_posix(),
        help="Project-relative Admin checks config path.",
    )
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT.as_posix(),
        help="Project-relative output directory for --write.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audit = build_audit(Path(args.config), REPO_ROOT)
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

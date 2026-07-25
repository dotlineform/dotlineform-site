#!/usr/bin/env python3
"""Build prepared public Mermaid theme pairs before public publish status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from docs_builder.runtime_bootstrap import apply_repo_local_env, projects_base_dir_from_argv

if __name__ == "__main__":
    apply_repo_local_env(projects_base_dir=projects_base_dir_from_argv(sys.argv[1:]))

from plan_public_mermaid_projection import (
    load_projection_planning_context,
    print_human_report,
)
from docs_artifact_locations import artifact_location_adapter
from docs_public_mermaid_producer import (
    DOCS_VIEWER_THEME_CSS_REL_PATH,
    produce_public_mermaid_projection,
)
from docs_public_mermaid_projection import public_mermaid_projection_report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build prepared public Mermaid light/dark pairs."
    )
    parser.add_argument("--scope", required=True, help="Configured public Docs Viewer scope.")
    parser.add_argument("--sub-scope", help="Configured public Docs Viewer sub-scope.")
    parser.add_argument(
        "--projects-base-dir",
        help="Override DOTLINEFORM_PROJECTS_BASE_DIR after loading .env.local.",
    )
    parser.add_argument("--write", action="store_true", help="Write verified prepared pairs and manifest.")
    parser.add_argument("--diagnostics", action="store_true", help="Print machine-readable build diagnostics.")
    return parser.parse_args(argv)


def print_build_report(result: dict[str, object]) -> None:
    summary = result["summary"]
    assert isinstance(summary, dict)
    print(f"Public Mermaid projection build (write) scope={result['scope']}")
    print(f"  diagrams prepared: {summary['successful_diagram_count']}")
    print(f"  variants prepared: {summary['published_variant_count']}")
    print(f"  variants removed: {summary['removed_variant_count']}")
    print(f"  failures: {summary['failure_count']}")
    for failure in result["failures"]:
        assert isinstance(failure, dict)
        print(
            f"  failed {failure.get('projection_id', '')} "
            f"stage={failure.get('stage', '')}: {failure.get('message', '')}"
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    try:
        context = load_projection_planning_context(
            repo_root,
            scope_id=args.scope,
            sub_scope_id=args.sub_scope or "",
        )
        if not args.write:
            print_human_report(context.plan, context.manifest_path, repo_root)
            if args.diagnostics:
                report = public_mermaid_projection_report(context.plan)
                print(
                    "Public Mermaid projection build diagnostics: "
                    + json.dumps(report, ensure_ascii=False, separators=(",", ":"))
                )
            return 0
        prepared = artifact_location_adapter(repo_root, context.prepared_location)
        result = produce_public_mermaid_projection(
            context.plan,
            prepared=prepared,
            write=True,
            theme_css_path=repo_root / DOCS_VIEWER_THEME_CSS_REL_PATH,
        )
    except (json.JSONDecodeError, OSError, RuntimeError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1

    print_build_report(result)
    if args.diagnostics:
        print(
            "Public Mermaid projection build diagnostics: "
            + json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        )
    return 1 if result["summary"]["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

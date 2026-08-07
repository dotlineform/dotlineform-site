#!/usr/bin/env python3
"""Migrate legacy Docs Viewer viewable front matter without rewriting bodies."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for import_path in (SERVICES_DIR,):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from docs_scope_config import (  # noqa: E402
    DocsScopeConfig,
    DocsSubScopeConfig,
    document_source_path,
    load_docs_scope_configs,
    resolve_scope_path,
)
from docs_source_model import (  # noqa: E402
    FRONT_MATTER_PATTERN,
    collection_supports_publishable,
    parse_front_matter_value,
    scope_markdown_paths,
    write_text_atomic,
)


FIELD_PATTERN = re.compile(r"^(?P<indent>[ \t]*)(?P<key>[A-Za-z0-9_]+)(?P<separator>[ \t]*:[ \t]*)(?P<value>.*?)(?P<newline>\r?\n)?$")


@dataclass(frozen=True)
class MigrationResult:
    text: str
    changed: bool
    legacy_value: bool | None


def migrate_source_text(
    source_text: str,
    *,
    publishable_supported: bool,
    source_name: str,
) -> MigrationResult:
    """Return an exact-body migration for one Markdown source."""

    match = FRONT_MATTER_PATTERN.match(source_text)
    if not match:
        raise ValueError(f"front matter could not be parsed in {source_name}")
    lines = match.group(1).splitlines(keepends=True)
    field_rows: dict[str, list[tuple[int, re.Match[str]]]] = {}
    for index, line in enumerate(lines):
        field_match = FIELD_PATTERN.match(line)
        if not field_match:
            continue
        field_rows.setdefault(field_match.group("key"), []).append((index, field_match))

    legacy_rows = field_rows.get("viewable", [])
    if not legacy_rows:
        return MigrationResult(source_text, False, None)
    if len(legacy_rows) != 1:
        raise ValueError(f"duplicate legacy viewable front matter in {source_name}")
    if field_rows.get("publishable"):
        raise ValueError(
            f"source contains both viewable and publishable front matter in {source_name}"
        )

    index, field_match = legacy_rows[0]
    legacy_value = parse_front_matter_value(field_match.group("value"))
    if not isinstance(legacy_value, bool):
        raise ValueError(f"legacy viewable front matter must be a boolean in {source_name}")
    if publishable_supported and legacy_value is False:
        newline = field_match.group("newline") or ""
        lines[index] = (
            f"{field_match.group('indent')}publishable"
            f"{field_match.group('separator')}false{newline}"
        )
    else:
        lines.pop(index)

    migrated_front_matter = "".join(lines)
    migrated_text = (
        source_text[: match.start(1)]
        + migrated_front_matter
        + source_text[match.end(1) :]
    )
    return MigrationResult(migrated_text, migrated_text != source_text, legacy_value)


def collection_label(scope: str, config: DocsScopeConfig | DocsSubScopeConfig) -> str:
    sub_scope = str(getattr(config, "sub_scope", "") or "").strip()
    return f"{scope}/{sub_scope}" if sub_scope else scope


def approved_local_false_values(values: list[str]) -> set[str]:
    approved = {str(value or "").strip() for value in values}
    if "" in approved:
        approved.remove("")
    return approved


def run_migration(
    repo_root: Path,
    *,
    scope_ids: list[str],
    write: bool,
    allow_local_false: set[str],
) -> dict[str, Any]:
    configs = load_docs_scope_configs(repo_root, scope_ids=scope_ids or None)
    planned: list[tuple[Path, str]] = []
    blockers: list[str] = []
    collection_counts: dict[str, int] = {}

    for scope, parent_config in configs.items():
        collections: list[DocsScopeConfig | DocsSubScopeConfig] = [
            parent_config,
            *parent_config.sub_scopes,
        ]
        for document_config in collections:
            label = collection_label(scope, document_config)
            source_root = resolve_scope_path(
                repo_root,
                document_source_path(document_config),
            )
            if not source_root.is_dir():
                raise FileNotFoundError(f"source root not found for {label}: {source_root}")
            changed = 0
            supports_publishable = collection_supports_publishable(document_config)
            for path in scope_markdown_paths(source_root):
                source_text = path.read_text(encoding="utf-8")
                result = migrate_source_text(
                    source_text,
                    publishable_supported=supports_publishable,
                    source_name=f"{label}/{path.name}",
                )
                if not result.changed:
                    continue
                if not supports_publishable and result.legacy_value is False:
                    approval_key = f"{label}:{path.stem}"
                    if approval_key not in allow_local_false:
                        blockers.append(approval_key)
                        continue
                planned.append((path, result.text))
                changed += 1
            collection_counts[label] = changed

    if blockers:
        raise ValueError(
            "local viewable:false values require explicit --allow-local-false approval: "
            + ", ".join(sorted(blockers))
        )
    if write:
        for path, source_text in planned:
            write_text_atomic(path, source_text)
    return {
        "mode": "write" if write else "dry-run",
        "changed": len(planned),
        "collections": collection_counts,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate legacy viewable front matter to public-only publishable.",
    )
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--allow-local-false",
        action="append",
        default=[],
        metavar="SCOPE[/SUB_SCOPE]:DOC_ID",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_migration(
        Path.cwd().resolve(),
        scope_ids=[str(scope or "").strip().lower() for scope in args.scope],
        write=args.write,
        allow_local_false=approved_local_false_values(args.allow_local_false),
    )
    print(
        f"Publishable front-matter migration ({result['mode']}): "
        f"{result['changed']} source file(s)"
    )
    for label, count in result["collections"].items():
        print(f"  {label}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

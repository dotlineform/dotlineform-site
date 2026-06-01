#!/usr/bin/env python3
"""Build the catalogue search index without Ruby."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_SCOPE = "catalogue"
SEARCH_BUILD_CONFIG_PATH = "studio/services/catalogue/search/build_config.json"
SEARCH_BUILD_TARGETED_POLICIES = {"full_rebuild", "record_update", "additive_only"}
SEARCH_BUILD_TARGETED_POLICY_OPERATIONS = {
    "record_update": {"create", "update", "delete"},
    "additive_only": {"create"},
}
CATALOGUE_TARGET_KINDS = {"moment", "series", "work"}
CATALOGUE_DEFAULTS = {
    "schema": "search_index_v1",
    "output_path": "assets/data/search/catalogue/index.json",
    "series_index_path": "assets/data/series_index.json",
    "works_index_path": "assets/data/works_index.json",
    "moments_index_path": "assets/data/moments_index.json",
}


@dataclass(frozen=True)
class CatalogueSearchTarget:
    kind: str
    id: str


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: Any) -> str:
    if value is None or value is False:
        return ""
    if value is True:
        return "true"
    return str(value).strip()


def normalize(value: Any) -> str:
    return normalize_text(value).lower()


def normalize_search_text(value: Any) -> str:
    return re.sub(r"\s+", " ", normalize_text(value).lower()).strip()


def normalize_string_array(values: Any) -> list[str]:
    if values is None:
        items: list[Any] = []
    elif isinstance(values, list):
        items = values
    else:
        items = [values]
    return [text for item in items if (text := normalize_text(item))]


def build_search_tokens(*values: Any) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for value in values:
        items = value if isinstance(value, list) else [value]
        for item in items:
            normalized = normalize_search_text(item)
            if not normalized:
                continue
            candidates = [normalized, *re.sub(r"[^a-z0-9]+", " ", normalized).split()]
            for candidate in candidates:
                token = normalize_search_text(candidate)
                if token and token not in seen:
                    seen.add(token)
                    tokens.append(token)
    return tokens


def json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def canonicalize_for_hash(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonicalize_for_hash(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    return value


def blake2b_payload_hash(payload: Any) -> str:
    canonical = json.dumps(canonicalize_for_hash(payload), ensure_ascii=False, separators=(",", ":"))
    return hashlib.blake2b(canonical.encode("utf-8"), digest_size=64).digest()[:16].hex()


def relative_path(path: Path | None, repo_root: Path) -> str:
    if path is None:
        return "(unknown path)"
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def numeric_aware_sort_key(value: Any) -> str:
    return re.sub(r"\d+", lambda match: match.group(0).rjust(3, "0"), normalize_text(value))


def empty_scalar(value: Any) -> bool:
    return value is None or (hasattr(value, "__len__") and len(value) == 0)


def catalogue_record_key(kind: Any, item_id: Any) -> str:
    return f"{normalize(kind)}:{normalize_text(item_id)}"


def catalogue_entry_key(entry: Any) -> str:
    if not isinstance(entry, dict):
        return ""
    return catalogue_record_key(entry.get("kind"), entry.get("id"))


class CatalogueSearchDataBuilder:
    def __init__(
        self,
        *,
        repo_root: Path,
        scope: str,
        output_path: Path | None = None,
        series_index_path: Path | None = None,
        works_index_path: Path | None = None,
        moments_index_path: Path | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.scope = normalize(scope)
        self.schema = CATALOGUE_DEFAULTS["schema"]
        self.output_path = self.resolve_path(output_path or CATALOGUE_DEFAULTS["output_path"])
        self.series_index_path = self.resolve_path(series_index_path or CATALOGUE_DEFAULTS["series_index_path"])
        self.works_index_path = self.resolve_path(works_index_path or CATALOGUE_DEFAULTS["works_index_path"])
        self.moments_index_path = self.resolve_path(moments_index_path or CATALOGUE_DEFAULTS["moments_index_path"])
        self.works_json_dir = self.resolve_path("assets/works/index")
        self.work_search_metadata_by_id: dict[str, dict[str, str]] = {}
        self.search_build_config: dict[str, Any] = {}

    def run(
        self,
        *,
        write: bool,
        force: bool,
        only_records: list[str] | None = None,
    ) -> dict[str, Any]:
        self.validate_scope()
        self.validate_search_build_config()
        target_records = self.normalize_target_catalogue_records(only_records)
        payload, diagnostics = self.build_catalogue_payload(target_records=target_records)
        self.validate_entry_source_families(payload)
        return self.write_payload(payload, write=write, force=force, diagnostics=diagnostics)

    def resolve_path(self, path: Path | str | None) -> Path | None:
        if path is None:
            return None
        return (self.repo_root / Path(path)).resolve()

    def validate_scope(self) -> None:
        if self.scope != "catalogue":
            raise SystemExit(f"Unsupported catalogue search scope: {self.scope}")

    def validate_search_build_config(self) -> None:
        config = self.load_json(self.resolve_path(SEARCH_BUILD_CONFIG_PATH))
        if not isinstance(config, dict):
            raise SystemExit("Invalid search build config: expected top-level object")
        self.search_build_config = config

        version = normalize_text(config.get("search_build_config_version"))
        if version != "search_build_config_v2":
            raise SystemExit(f"Invalid search build config version: {version or '(missing)'}")

        source_families = config.get("source_families")
        if not isinstance(source_families, dict) or not source_families:
            raise SystemExit("Invalid search build config: expected source_families object")
        self.validate_source_families(source_families)

        scopes = config.get("scopes")
        if not isinstance(scopes, dict) or "catalogue" not in scopes:
            raise SystemExit("Invalid search build config: expected catalogue scope")
        self.validate_scope_build_config(scopes["catalogue"], source_families)

    def validate_source_families(self, source_families: dict[str, Any]) -> None:
        for family_id, raw_family in source_families.items():
            if not isinstance(raw_family, dict):
                raise SystemExit(f"Invalid search build config: source family {family_id} must be an object")
            scopes = raw_family.get("scopes")
            if not isinstance(scopes, list) or [normalize(scope) for scope in scopes] != ["catalogue"]:
                raise SystemExit(f"Invalid search build config: source family {family_id} must be catalogue-owned")
            self.validate_targeted_policy(raw_family, f"source family {family_id}")
            if normalize_text(raw_family.get("fallback")) != "full_rebuild":
                raise SystemExit(f"Invalid search build config: source family {family_id} fallback must be full_rebuild")

    def validate_scope_build_config(self, scope_config: Any, source_families: dict[str, Any]) -> None:
        if not isinstance(scope_config, dict):
            raise SystemExit("Invalid search build config: catalogue scope must be an object")
        fields = scope_config.get("fields")
        if not isinstance(fields, dict) or not fields:
            raise SystemExit("Invalid search build config: catalogue scope needs fields")
        self.validate_targeted_policy(scope_config, "scope catalogue")

        for field_name, field_config in fields.items():
            if not isinstance(field_config, dict):
                raise SystemExit(f"Invalid search build config: field catalogue.{field_name} must be an object")
            families = [normalize_text(family) for family in field_config.get("source_families") or []]
            families = [family for family in families if family]
            if not families:
                raise SystemExit(f"Invalid search build config: field catalogue.{field_name} needs source_families")
            unknown_family = next((family for family in families if family not in source_families), "")
            if unknown_family:
                raise SystemExit(
                    f"Invalid search build config: field catalogue.{field_name} "
                    f"references unknown source family {unknown_family}"
                )

    def validate_targeted_policy(self, config: dict[str, Any], label: str) -> None:
        if "targeted" in config:
            raise SystemExit(f"Invalid search build config: {label} uses obsolete targeted boolean; use targeted_policy")

        policy = normalize_text(config.get("targeted_policy"))
        if policy not in SEARCH_BUILD_TARGETED_POLICIES:
            policies = ", ".join(["full_rebuild", "record_update", "additive_only"])
            raise SystemExit(f"Invalid search build config: {label} targeted_policy must be one of {policies}")

        operations = config.get("targeted_operations")
        if policy == "full_rebuild":
            if operations:
                raise SystemExit(
                    f"Invalid search build config: {label} targeted_operations is only valid for targeted policies"
                )
            return

        if not isinstance(operations, list) or not all(normalize_text(operation) for operation in operations):
            raise SystemExit(
                f"Invalid search build config: {label} targeted_operations must be a non-empty string array"
            )
        supported = SEARCH_BUILD_TARGETED_POLICY_OPERATIONS[policy]
        unsupported = next((normalize_text(operation) for operation in operations if normalize_text(operation) not in supported), "")
        if unsupported:
            raise SystemExit(
                f"Invalid search build config: {label} targeted_operations includes unsupported {unsupported} for {policy}"
            )

    def validate_entry_source_families(self, payload: dict[str, Any]) -> None:
        scope_config = self.search_build_config.get("scopes", {}).get("catalogue")
        fields = scope_config.get("fields") if isinstance(scope_config, dict) else None
        if not isinstance(fields, dict):
            raise SystemExit("Invalid search build config: catalogue fields unavailable")

        entries = payload.get("entries")
        if not isinstance(entries, list):
            return
        emitted_fields = sorted({key for entry in entries if isinstance(entry, dict) for key in entry})
        missing_fields = [field for field in emitted_fields if field not in fields]
        if missing_fields:
            raise SystemExit(
                "Invalid search build config: catalogue missing field source declarations for "
                + ", ".join(missing_fields)
            )

    def build_catalogue_payload(
        self,
        *,
        target_records: list[CatalogueSearchTarget] | None,
    ) -> tuple[dict[str, Any], dict[str, int] | None]:
        target_records = target_records or []
        series_payload = self.load_index_hash(self.series_index_path, "series")
        works_payload = self.load_index_hash(self.works_index_path, "works")
        moments_payload = self.load_index_hash(self.moments_index_path, "moments")
        series_title_by_id = {
            series_id: normalize_text(row.get("title")) for series_id, row in series_payload.items()
        }

        entries: list[dict[str, Any]] = []
        for series_id in sorted(series_payload):
            series_record = series_payload[series_id]
            title = normalize_text(series_record.get("title")) or series_id
            entries.append(
                self.build_catalogue_entry(
                    kind="series",
                    item_id=series_id,
                    title=title,
                    href=f"/series/?series={series_id}",
                    year=series_record.get("year"),
                    display_meta=normalize_text(series_record.get("year_display")),
                    series_type=normalize_text(series_record.get("series_type")),
                )
            )

        for work_id in sorted(works_payload):
            work_record = works_payload[work_id]
            work_search_metadata = self.resolve_work_search_metadata(work_id)
            series_ids = normalize_string_array(work_record.get("series_ids"))
            series_titles = [series_title_by_id.get(series_id, series_id) for series_id in series_ids]
            title = normalize_text(work_record.get("title")) or work_id
            entries.append(
                self.build_catalogue_entry(
                    kind="work",
                    item_id=work_id,
                    title=title,
                    href=f"/works/?work={work_id}",
                    year=work_record.get("year"),
                    display_meta=normalize_text(work_record.get("year_display")),
                    series_ids=series_ids,
                    series_titles=series_titles,
                    medium_type=work_search_metadata["medium_type"],
                    medium_caption=work_search_metadata["medium_caption"],
                )
            )

        for moment_id in sorted(moments_payload):
            moment_record = moments_payload[moment_id]
            date = normalize_text(moment_record.get("date"))
            display_meta = normalize_text(moment_record.get("date_display")) or date
            title = normalize_text(moment_record.get("title")) or moment_id
            entries.append(
                self.build_catalogue_entry(
                    kind="moment",
                    item_id=moment_id,
                    title=title,
                    href=f"/moments/{moment_id}/",
                    date=date,
                    display_meta=display_meta,
                )
            )

        ordered_entries = sorted(
            entries,
            key=lambda entry: (
                normalize_text(entry.get("kind")),
                numeric_aware_sort_key(entry.get("title")),
                normalize_text(entry.get("id")),
            ),
        )
        if not target_records:
            return self.build_catalogue_search_payload(ordered_entries), None
        return self.build_targeted_catalogue_payload(ordered_entries, target_records)

    def load_index_hash(self, path: Path | None, key: str) -> dict[str, dict[str, Any]]:
        payload = self.load_json(path)
        rows = payload.get(key) if isinstance(payload, dict) else None
        if not isinstance(rows, dict):
            raise SystemExit(f"Invalid {key} index payload: expected top-level {key} object")
        return {str(row_key): row if isinstance(row, dict) else {} for row_key, row in rows.items()}

    def load_json(self, path: Path | None) -> Any:
        if not path or not path.exists():
            raise SystemExit(f"Source JSON not found: {relative_path(path, self.repo_root)}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Failed to parse JSON: {relative_path(path, self.repo_root)} ({exc})") from exc

    def build_targeted_catalogue_payload(
        self,
        entries: list[dict[str, Any]],
        target_records: list[CatalogueSearchTarget],
    ) -> tuple[dict[str, Any], dict[str, int]]:
        existing_payload = self.load_existing_search_payload()
        if not existing_payload or not isinstance(existing_payload.get("entries"), list):
            diagnostics = {"changed": len(entries), "removed": 0, "unchanged": 0, "full_fallback": 1}
            return self.build_catalogue_search_payload(entries), diagnostics

        existing_entries = existing_payload["entries"]
        entry_by_key = {catalogue_entry_key(entry): entry for entry in entries}
        order_by_key = {catalogue_entry_key(entry): index for index, entry in enumerate(entries)}
        existing_by_key: dict[str, dict[str, Any]] = {}
        for entry in existing_entries:
            if not isinstance(entry, dict):
                continue
            entry_key = catalogue_entry_key(entry)
            if entry_key:
                existing_by_key[entry_key] = entry
        existing_order_by_key = {
            catalogue_entry_key(entry): index for index, entry in enumerate(existing_entries)
            if isinstance(entry, dict)
        }

        changed = 0
        unchanged = 0
        for target in target_records:
            target_key = catalogue_record_key(target.kind, target.id)
            next_entry = entry_by_key.get(target_key)
            if next_entry is None:
                raise SystemExit(f"Targeted catalogue search create could not find source record {target_key}")

            current_entry = existing_by_key.get(target_key)
            if current_entry is None:
                existing_by_key[target_key] = next_entry
                changed += 1
            elif current_entry == next_entry:
                unchanged += 1
            else:
                raise SystemExit(
                    f"Targeted catalogue search is additive-only; existing record {target_key} "
                    "requires a full catalogue search rebuild"
                )

        merged_entries = sorted(
            existing_by_key.values(),
            key=lambda entry: (
                order_by_key.get(
                    catalogue_entry_key(entry),
                    len(entries) + existing_order_by_key.get(catalogue_entry_key(entry), 0),
                ),
                existing_order_by_key.get(catalogue_entry_key(entry), len(existing_entries)),
            ),
        )
        diagnostics = {"changed": changed, "removed": 0, "unchanged": unchanged, "full_fallback": 0}
        return self.build_catalogue_search_payload(merged_entries), diagnostics

    def build_catalogue_search_payload(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        version_payload = {"schema": self.schema, "entries": entries}
        version = f"blake2b-{blake2b_payload_hash(version_payload)}"
        return {
            "header": {
                "schema": self.schema,
                "version": version,
                "generated_at_utc": utc_timestamp(),
                "count": len(entries),
            },
            "entries": entries,
        }

    def build_catalogue_entry(
        self,
        *,
        kind: str,
        item_id: str,
        title: str,
        href: str,
        year: Any = None,
        date: Any = None,
        display_meta: Any = None,
        series_ids: Any = None,
        series_titles: Any = None,
        medium_type: Any = None,
        medium_caption: Any = None,
        series_type: Any = None,
    ) -> dict[str, Any]:
        normalized_series_ids = normalize_string_array(series_ids)
        normalized_series_titles = normalize_string_array(series_titles)
        search_terms = build_search_tokens(
            item_id,
            title,
            display_meta,
            None if year is None else str(year),
            date,
            normalized_series_ids,
            normalized_series_titles,
            medium_type,
            medium_caption,
            series_type,
        )
        entry = {
            "kind": kind,
            "id": normalize_text(item_id),
            "title": normalize_text(title),
            "href": normalize_text(href),
            "year": year,
            "date": normalize_text(date),
            "display_meta": normalize_text(display_meta),
            "series_ids": normalized_series_ids,
            "series_titles": normalized_series_titles,
            "medium_type": normalize_text(medium_type),
            "series_type": normalize_text(series_type),
            "search_terms": search_terms,
            "search_text": " ".join(search_terms),
        }
        return {key: value for key, value in entry.items() if not self.compact_catalogue_field(key, value)}

    def compact_catalogue_field(self, key: str, value: Any) -> bool:
        if key in {"series_ids", "series_titles"}:
            return False
        return empty_scalar(value)

    def resolve_work_search_metadata(self, work_id: str) -> dict[str, str]:
        cached = self.work_search_metadata_by_id.get(work_id)
        if cached:
            return cached

        metadata = {"medium_type": "", "medium_caption": ""}
        work_json_path = self.works_json_dir / f"{work_id}.json" if self.works_json_dir else None
        if not work_json_path or not work_json_path.exists():
            self.work_search_metadata_by_id[work_id] = metadata
            return metadata

        payload = self.load_json(work_json_path)
        work_payload = payload.get("work") if isinstance(payload, dict) else None
        if isinstance(work_payload, dict):
            metadata["medium_type"] = normalize_text(work_payload.get("medium_type"))
            metadata["medium_caption"] = normalize_text(work_payload.get("medium_caption"))
        self.work_search_metadata_by_id[work_id] = metadata
        return metadata

    def write_payload(
        self,
        payload: dict[str, Any],
        *,
        write: bool,
        force: bool,
        diagnostics: dict[str, int] | None,
    ) -> dict[str, Any]:
        count = payload.get("header", {}).get("count")
        relative_output_path = relative_path(self.output_path, self.repo_root)
        existing_version = self.extract_existing_version(self.output_path)
        payload_version = payload.get("header", {}).get("version")
        targeted_changes = diagnostics is not None and (
            int(diagnostics.get("changed", 0)) > 0 or int(diagnostics.get("removed", 0)) > 0
        )
        if existing_version == payload_version and not force and not targeted_changes:
            self.print_skip_message(relative_output_path, write, diagnostics)
            return payload
        if not write:
            self.print_dry_run_message(relative_output_path, count, diagnostics)
            return payload
        if self.output_path is None:
            raise SystemExit("Generated search index output path is required")
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(json_text(payload), encoding="utf-8")
        self.print_write_message(relative_output_path, count, diagnostics)
        return payload

    def print_skip_message(self, relative_output_path: str, write: bool, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            verb = "Wrote" if write else "Would write"
            print(
                "Targeted search index JSON done. "
                f"{verb}: 0. Skipped: 1. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        if write:
            print(f"Search index JSON done. Wrote: 0. Skipped: 1. Path: {relative_output_path}")
        else:
            print(f"Search index JSON done. Would write: 0. Skipped: 1. Path: {relative_output_path}")

    def print_dry_run_message(self, relative_output_path: str, count: int, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            print(f"Targeted dry run: {count} {self.scope} search entries")
            print(
                f"Would write: 1. Skipped: 0. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        print(f"Dry run: {count} {self.scope} search entries")
        print(f"Would write: {relative_output_path}")

    def print_write_message(self, relative_output_path: str, count: int, diagnostics: dict[str, int] | None) -> None:
        if diagnostics:
            print(
                "Targeted search index JSON done. "
                f"Wrote: 1. Skipped: 0. Changed: {diagnostics['changed']}. "
                f"Removed: {diagnostics['removed']}. Unchanged: {diagnostics['unchanged']}. "
                f"Full fallback: {diagnostics['full_fallback']}. Path: {relative_output_path}"
            )
            return
        print(f"Wrote {relative_output_path} with {count} {self.scope} search entries")

    def extract_existing_version(self, path: Path | None) -> str | None:
        if not path or not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        header = payload.get("header") if isinstance(payload, dict) else None
        return normalize_text(header.get("version")) if isinstance(header, dict) else None

    def load_existing_search_payload(self) -> dict[str, Any] | None:
        if not self.output_path or not self.output_path.exists():
            return None
        try:
            payload = json.loads(self.output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None

    def normalize_target_catalogue_records(self, values: list[str] | tuple[str, ...] | None) -> list[CatalogueSearchTarget]:
        seen: set[str] = set()
        targets: list[CatalogueSearchTarget] = []
        for value in values or []:
            for raw_record in normalize_text(value).split(","):
                record = normalize_text(raw_record)
                if not record:
                    continue
                parts = [normalize_text(part) for part in record.split(":", 1)]
                if len(parts) != 2 or not parts[0] or not parts[1]:
                    raise SystemExit("Targeted catalogue records must use kind:id form")
                kind = normalize(parts[0])
                item_id = parts[1]
                if kind not in CATALOGUE_TARGET_KINDS:
                    kinds = ", ".join(["moment", "series", "work"])
                    raise SystemExit(f"Targeted catalogue record kind must be one of {kinds}")
                key = catalogue_record_key(kind, item_id)
                if key in seen:
                    continue
                seen.add(key)
                targets.append(CatalogueSearchTarget(kind=kind, id=item_id))
        return targets


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build catalogue search indexes.")
    parser.add_argument("--scope", default=DEFAULT_SCOPE, help="Catalogue search scope to build.")
    parser.add_argument("--source-index", help="Docs Viewer-only source index path.")
    parser.add_argument("--series-index", help="Canonical series index JSON path for catalogue scope.")
    parser.add_argument("--works-index", help="Canonical works index JSON path for catalogue scope.")
    parser.add_argument("--moments-index", help="Canonical moments index JSON path for catalogue scope.")
    parser.add_argument("--output", help="Generated search index output path.")
    parser.add_argument("--only-doc-ids", help="Docs Viewer-only targeted search ids.")
    parser.add_argument(
        "--only-records",
        action="append",
        default=[],
        help="Comma-separated kind:id records for additive catalogue search updates.",
    )
    parser.add_argument("--remove-missing", action="store_true", help="Docs Viewer-only targeted missing-record removal.")
    parser.add_argument("--write", action="store_true", help="Persist generated files; default is dry-run.")
    parser.add_argument("--force", action="store_true", help="Write even when the content version matches.")
    args = parser.parse_args(argv)
    if args.source_index is not None:
        raise SystemExit("Catalogue search does not support --source-index")
    if args.only_doc_ids is not None:
        raise SystemExit("Catalogue search does not support --only-doc-ids")
    if args.remove_missing:
        raise SystemExit("Catalogue search does not support --remove-missing")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    builder = CatalogueSearchDataBuilder(
        repo_root=repo_root,
        scope=args.scope,
        output_path=Path(args.output) if args.output else None,
        series_index_path=Path(args.series_index) if args.series_index else None,
        works_index_path=Path(args.works_index) if args.works_index else None,
        moments_index_path=Path(args.moments_index) if args.moments_index else None,
    )
    builder.run(write=args.write, force=args.force, only_records=args.only_records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

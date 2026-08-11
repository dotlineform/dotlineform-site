from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

from .common import load_site_tools_config, read_text, write_text
from .semantic_token_registry import (
    SemanticTokenFamily,
    SemanticTokenTargetType,
    load_semantic_token_registry,
    normalize_semantic_token_id,
)
from pipeline_config import load_pipeline_config  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
STUDIO_SERVICES_DIR = REPO_ROOT / "studio" / "services"
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
for module_dir in (STUDIO_SERVICES_DIR, DOCS_SERVICES_DIR):
    if str(module_dir) not in sys.path:
        sys.path.insert(0, str(module_dir))

from tags import tag_alias_mutations  # noqa: E402
from tags import tag_document_declarations  # noqa: E402
from tags import tag_source_model  # noqa: E402


SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION = "docs_semantic_token_target_lookup_v2"
DEFAULT_SEMANTIC_TARGET_LOOKUP_PATH = Path(
    "docs-viewer/data/generated/semantic-tokens/target-lookup.json"
)

CATALOGUE_KIND_SOURCES = {
    "work": {
        "filename": "works.json",
        "root_key": "works",
        "id_field": "work_id",
    },
    "series": {
        "filename": "series.json",
        "root_key": "series",
        "id_field": "series_id",
    },
}

CATALOGUE_TARGET_DESTINATIONS = {
    "catalogue-work-target-lookup": ("/works/", "work"),
    "catalogue-series-target-lookup": ("/series/", "series"),
}


def compact_json_text(payload: Any) -> str:
    targets = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(targets, list):
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    lines = [
        "{",
        f'  "schema_version": {json.dumps(payload.get("schema_version"), ensure_ascii=False)},',
        '  "targets": [',
    ]
    for index, target in enumerate(targets):
        suffix = "," if index < len(targets) - 1 else ""
        lines.append(f"    {json.dumps(target, ensure_ascii=False, separators=(',', ':'))}{suffix}")
    lines.extend(["  ]", "}"])
    return "\n".join(lines) + "\n"


def normalize_lookup_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def json_rows(payload: Any, root_key: str) -> list[dict[str, Any]]:
    records = payload.get(root_key) if isinstance(payload, dict) else None
    rows = records.values() if isinstance(records, dict) else records if isinstance(records, list) else []
    return [dict(row) for row in rows if isinstance(row, dict)]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def is_published(record: dict[str, Any]) -> bool:
    return str(record.get("status") or "").strip().lower() == "published"


def positive_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 and str(value).strip() == str(parsed) else None


def browser_safe_image_src(value: Any) -> str:
    src = str(value or "").strip()
    if not src:
        return ""
    if src.startswith("/") and not src.startswith("//"):
        return src
    parsed = urlsplit(src)
    if (
        parsed.scheme == "https"
        and parsed.netloc
        and parsed.username is None
        and parsed.password is None
    ):
        return src
    return ""


def browser_safe_href(value: Any) -> str:
    href = str(value or "").strip()
    if not href.startswith("/") or href.startswith("//"):
        return ""
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or parsed.fragment:
        return ""
    return href


def aliases_by_tag_id(
    registry_payload: dict[str, Any],
    aliases_payload: dict[str, Any],
    *,
    canonical_tag_ids: set[str],
) -> dict[str, list[str]]:
    if aliases_payload.get("tag_aliases_version") != tag_source_model.TAG_ALIASES_VERSION:
        raise ValueError(
            f"Tag aliases must use {tag_source_model.TAG_ALIASES_VERSION}"
        )
    tag_alias_mutations.validate_alias_entries(aliases_payload, registry_payload)
    aliases_by_tag = {tag_id: [] for tag_id in canonical_tag_ids}
    for index, (raw_alias, raw_entry) in enumerate(aliases_payload["aliases"].items()):
        alias = tag_source_model.sanitize_alias_key(raw_alias, index)
        entry = tag_source_model.sanitize_alias_entry(
            raw_entry,
            alias,
            "tag_aliases.aliases",
        )
        for tag_id in entry["tags"]:
            aliases_by_tag[tag_id].append(alias)
    for aliases in aliases_by_tag.values():
        aliases.sort()
    return aliases_by_tag


def public_tag_document_location(document: dict[str, Any]) -> dict[str, str] | None:
    for raw_location in document.get("locations", []):
        if not isinstance(raw_location, dict):
            continue
        if str(raw_location.get("access") or "") != "public":
            continue
        href = browser_safe_href(raw_location.get("url"))
        title = str(raw_location.get("title") or "").strip()
        return {"href": href, "title": title} if href and title else None
    return None


def tag_target_rows(
    family: SemanticTokenFamily,
    target_type: SemanticTokenTargetType,
    *,
    registry_payload: Any,
    aliases_payload: Any,
    associations_payload: Any,
) -> list[dict[str, Any]]:
    if target_type.lookup_adapter != "tag-target-lookup":
        return []
    tag_rows = registry_payload["tags"]
    aliases = aliases_by_tag_id(
        registry_payload,
        aliases_payload,
        canonical_tag_ids={row["tag_id"] for row in tag_rows},
    )
    documents_by_tag = {
        association["tag_id"]: association["documents"]
        for association in associations_payload["associations"]
    }
    targets: list[dict[str, Any]] = []
    for tag_row_record in tag_rows:
        tag_id = normalize_semantic_token_id(
            tag_row_record["tag_id"],
            target_type.id_policy,
        )
        if tag_id is None:
            raise ValueError(
                f"Tag {tag_row_record['tag_id']!r} does not match the semantic-token policy"
            )
        documents = documents_by_tag.get(tag_id, [])
        if not documents:
            continue
        chosen = documents[0]
        primary = tag_row_record.get("primary_document")
        if primary is not None:
            chosen = next(
                (
                    document
                    for document in documents
                    if document["target"] == primary
                ),
                chosen,
            )
        location = public_tag_document_location(chosen)
        if location is None:
            continue
        targets.append(
            {
                "family": family.key,
                "target_type": target_type.key,
                "target_id": tag_id,
                "title": tag_id,
                "href": location["href"],
                "meta": [tag_row_record["group"], location["title"]],
                "aliases": aliases[tag_id],
            }
        )
    return targets


def primary_image_settings(
    repo_root: Path,
    *,
    media_path_key: str = "image_works",
) -> dict[str, Any]:
    site_config = load_site_tools_config(repo_root)
    pipeline_config = load_pipeline_config(repo_root=repo_root)
    media = site_config.get("media") if isinstance(site_config.get("media"), dict) else {}
    variants = (
        pipeline_config.get("variants")
        if isinstance(pipeline_config.get("variants"), dict)
        else {}
    )
    primary = variants.get("primary") if isinstance(variants.get("primary"), dict) else {}
    encoding = (
        pipeline_config.get("encoding")
        if isinstance(pipeline_config.get("encoding"), dict)
        else {}
    )
    width = positive_integer(primary.get("preferred_width"))
    suffix = str(primary.get("suffix") or "").strip().lower()
    image_format = str(encoding.get("format") or "").strip().lower()
    media_base = str(media.get("base") or "").strip().rstrip("/")
    image_path = "/" + str(media.get(media_path_key) or "").strip().strip("/")
    if not width or not re.fullmatch(r"[a-z0-9-]+", suffix):
        raise ValueError("primary image pipeline settings are invalid")
    if not re.fullmatch(r"[a-z0-9]+", image_format):
        raise ValueError("primary image format is invalid")
    if media_base and not browser_safe_image_src(f"{media_base}/"):
        raise ValueError("primary image media base must be HTTPS")
    if image_path == "/":
        raise ValueError("primary image media path is unavailable")
    return {
        "base": media_base,
        "path": image_path,
        "width": width,
        "suffix": suffix,
        "format": image_format,
    }


def work_primary_image_src(
    record: dict[str, Any],
    work_id: str,
    settings: dict[str, Any],
) -> str:
    if (
        not is_published(record)
        or not str(record.get("project_filename") or "").strip()
        or positive_integer(record.get("width_px")) is None
        or positive_integer(record.get("height_px")) is None
    ):
        return ""
    media_version = positive_integer(record.get("media_version"))
    if media_version is None:
        return ""
    filename = (
        f"{work_id}-{settings['suffix']}-{settings['width']}.{settings['format']}"
    )
    return browser_safe_image_src(
        f"{settings['base']}{settings['path']}/{quote(filename)}?v={media_version}"
    )


def series_primary_image_src(
    record: dict[str, Any],
    series_id: str,
    *,
    works_by_id: dict[str, dict[str, Any]],
    settings: dict[str, Any],
) -> str:
    primary_work_id = str(record.get("primary_work_id") or "").strip()
    primary_work = works_by_id.get(primary_work_id)
    if primary_work is None or not is_published(primary_work):
        return ""
    series_ids = primary_work.get("series_ids")
    if not isinstance(series_ids, list) or series_id not in {
        str(value or "").strip() for value in series_ids
    }:
        return ""
    return work_primary_image_src(primary_work, primary_work_id, settings)


def display_date(record: dict[str, Any]) -> str:
    for field in ("year_display", "date_display", "year", "date"):
        value = str(record.get(field) or "").strip()
        if value:
            return value
    return ""


def series_titles_by_id(series_rows: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in series_rows:
        series_id = str(row.get("series_id") or "").strip()
        title = str(row.get("title") or "").strip()
        if series_id and title:
            out[series_id] = title
    return out


def first_series_title(record: dict[str, Any], series_titles: dict[str, str]) -> str:
    series_ids = record.get("series_ids")
    if not isinstance(series_ids, list):
        return ""
    for raw_id in series_ids:
        series_id = str(raw_id or "").strip()
        title = series_titles.get(series_id)
        if title:
            return title
    return ""


def target_meta(kind: str, record: dict[str, Any], *, series_titles: dict[str, str]) -> list[str]:
    meta: list[str] = []
    date_value = display_date(record)
    if date_value:
        meta.append(date_value)
    if kind == "work":
        series_title = first_series_title(record, series_titles)
        if series_title and series_title not in meta:
            meta.append(series_title)
    return meta


def target_row(
    family: SemanticTokenFamily,
    target_type: SemanticTokenTargetType,
    record: dict[str, Any],
    source: dict[str, Any],
    *,
    series_titles: dict[str, str],
    image_src: str = "",
    has_details: bool = False,
) -> dict[str, Any] | None:
    if not is_published(record):
        return None
    id_field = str(source["id_field"])
    normalized_id = normalize_semantic_token_id(str(record.get(id_field) or ""), target_type.id_policy)
    title = str(record.get("title") or "").strip()
    href = semantic_token_target_href(target_type, normalized_id or "")
    if not normalized_id or not title or not href:
        return None
    row = {
        "family": family.key,
        "target_type": target_type.key,
        "target_id": normalized_id,
        "title": title,
        "href": href,
        "meta": target_meta(target_type.key, record, series_titles=series_titles),
    }
    if has_details:
        row["has_details"] = True
    if image_src:
        row["image"] = {"src": image_src}
    return row


def semantic_token_target_href(target_type: SemanticTokenTargetType, target_id: str) -> str:
    destination = CATALOGUE_TARGET_DESTINATIONS.get(target_type.lookup_adapter)
    if destination is None or not target_id:
        return ""
    path, parameter = destination
    return f"{path}?{quote(parameter)}={quote(target_id)}"


class SemanticTargetLookupBuilder:
    def __init__(self, *, repo_root: Path, output_path: Path | None = None) -> None:
        self.repo_root = repo_root.resolve()
        self.output_path = self.repo_root / (output_path or DEFAULT_SEMANTIC_TARGET_LOOKUP_PATH)

    def run(self, *, write: bool) -> dict[str, Any]:
        payload = self.payload()
        text = compact_json_text(payload)
        changed = read_text(self.output_path) != text
        if write and changed:
            write_text(self.output_path, text)
        diagnostics = {
            "target_count": len(payload["targets"]),
            "changed": changed,
            "wrote": bool(write and changed),
            "output_path": self.output_path.relative_to(self.repo_root).as_posix(),
        }
        return {"payload": payload, "diagnostics": diagnostics}

    def payload(self) -> dict[str, Any]:
        registry = load_semantic_token_registry(self.repo_root)
        targets: list[dict[str, Any]] = []
        if registry is None:
            return {
                "schema_version": SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION,
                "targets": [],
            }
        catalogue_family = registry.family("catalogue")
        if catalogue_family is not None:
            source_root = (
                self.repo_root / "studio" / "data" / "canonical" / "catalogue"
            )
            image_settings = primary_image_settings(self.repo_root)
            work_source = CATALOGUE_KIND_SOURCES["work"]
            work_payload = load_json(source_root / str(work_source["filename"]))
            work_rows = json_rows(work_payload, str(work_source["root_key"]))
            works_by_id = {
                str(row.get("work_id") or "").strip(): row
                for row in work_rows
                if str(row.get("work_id") or "").strip()
            }
            series_source = CATALOGUE_KIND_SOURCES["series"]
            series_payload = load_json(
                source_root / str(series_source["filename"])
            )
            series_rows = json_rows(
                series_payload,
                str(series_source["root_key"]),
            )
            series_titles = series_titles_by_id(series_rows)
            for target_type in catalogue_family.target_types:
                source = CATALOGUE_KIND_SOURCES.get(target_type.key)
                if source is None:
                    continue
                rows = work_rows if target_type.key == "work" else series_rows
                for record in rows:
                    normalized_id = normalize_semantic_token_id(
                        str(record.get(source["id_field"]) or ""),
                        target_type.id_policy,
                    ) or ""
                    image_src = ""
                    if target_type.key == "work":
                        image_src = work_primary_image_src(
                            record,
                            normalized_id,
                            image_settings,
                        )
                    elif target_type.key == "series":
                        image_src = series_primary_image_src(
                            record,
                            normalized_id,
                            works_by_id=works_by_id,
                            settings=image_settings,
                        )
                    row = target_row(
                        catalogue_family,
                        target_type,
                        record,
                        source,
                        series_titles=series_titles,
                        image_src=image_src,
                        has_details=(
                            target_type.key == "work"
                            and (
                                source_root
                                / "work_details"
                                / f"{normalized_id}.json"
                            ).is_file()
                        ),
                    )
                    if row is not None:
                        targets.append(row)

        tag_family = registry.family("tag")
        if tag_family is not None:
            tag_target_type = tag_family.target_type("tag")
            if tag_target_type is not None:
                targets.extend(
                    tag_target_rows(
                        tag_family,
                        tag_target_type,
                        registry_payload=tag_source_model.load_registry(
                            self.repo_root / tag_source_model.REGISTRY_REL_PATH
                        ),
                        aliases_payload=tag_source_model.load_aliases(
                            self.repo_root / tag_source_model.ALIASES_REL_PATH
                        ),
                        associations_payload=(
                            tag_document_declarations.load_tag_document_association_payload(
                                self.repo_root
                            )
                        ),
                    )
                )
        targets.sort(
            key=lambda row: (
                registry.family(row["family"]).order
                if registry.family(row["family"])
                else 999,
                registry.family(row["family"]).target_type(
                    row["target_type"]
                ).order
                if registry.family(row["family"])
                and registry.family(row["family"]).target_type(
                    row["target_type"]
                )
                else 999,
                normalize_lookup_text(row["title"]),
                row["target_id"],
            )
        )
        return {
            "schema_version": SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION,
            "targets": targets,
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer semantic-token target lookup data.")
    parser.add_argument("--output", help="Override semantic target lookup output path.")
    parser.add_argument("--write", action="store_true", help="Write generated lookup data.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    builder = SemanticTargetLookupBuilder(
        repo_root=Path.cwd(),
        output_path=Path(args.output) if args.output else None,
    )
    result = builder.run(write=args.write)
    diagnostics = result["diagnostics"]
    mode = "write" if args.write else "dry-run"
    verb = "wrote" if diagnostics["wrote"] else "would write" if diagnostics["changed"] else "unchanged"
    print(f"Semantic target lookup ({mode})")
    print(f"  targets total: {diagnostics['target_count']}")
    print(f"  output: {diagnostics['output_path']}")
    print(f"  status: {verb}")
    return 0

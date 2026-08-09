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
        family = registry.family("catalogue")
        if family is None:
            return {
                "schema_version": SEMANTIC_TARGET_LOOKUP_SCHEMA_VERSION,
                "targets": [],
            }
        source_root = self.repo_root / "studio" / "data" / "canonical" / "catalogue"
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
        series_payload = load_json(source_root / str(series_source["filename"]))
        series_rows = json_rows(series_payload, str(series_source["root_key"]))
        series_titles = series_titles_by_id(series_rows)
        for target_type in family.target_types:
            source = CATALOGUE_KIND_SOURCES.get(target_type.key)
            if source is not None:
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
                        family,
                        target_type,
                        record,
                        source,
                        series_titles=series_titles,
                        image_src=image_src,
                        has_details=(
                            target_type.key == "work"
                            and (source_root / "work_details" / f"{normalized_id}.json").is_file()
                        ),
                    )
                    if row is not None:
                        targets.append(row)
                continue
        targets.sort(
            key=lambda row: (
                family.target_type(row["target_type"]).order
                if family.target_type(row["target_type"])
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

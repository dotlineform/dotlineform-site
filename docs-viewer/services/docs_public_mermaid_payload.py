#!/usr/bin/env python3
"""Assemble verified Mermaid theme pairs into public-only document payload bytes."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping

from docs_mermaid_renderer import RenderedMermaidSvg, inspect_sanitized_mermaid_svg
from docs_public_mermaid_projection import (
    PUBLIC_MERMAID_THEMES,
    validate_public_mermaid_manifest,
)
from docs_svg_sanitizer import sanitize_svg_bytes


PUBLIC_MERMAID_PREPARED_RELATIVE_PATH = Path(".publish/public-mermaid-projection")
PUBLIC_MERMAID_MANIFEST_FILENAME = "manifest.json"
PUBLIC_MERMAID_HTML_FENCE_PATTERN = re.compile(
    r'<pre><code class="language-mermaid">(?P<source>.*?)</code></pre>',
    re.DOTALL,
)


@dataclass(frozen=True)
class PreparedPublicMermaidProjection:
    records_by_doc_id: Mapping[str, tuple[dict[str, Any], ...]]
    variant_bytes_by_projection_id: Mapping[str, Mapping[str, bytes]]
    projection_ids: frozenset[str]


def _source_digest(source: str) -> str:
    return f"sha256:{hashlib.sha256(source.encode('utf-8')).hexdigest()}"


def _validated_variant(
    prepared_root: Path,
    record: Mapping[str, Any],
    theme: str,
) -> RenderedMermaidSvg:
    projection_id = str(record["projection_id"])
    variant = record["variants"][theme]
    identity = str(variant["artifact_identity"])
    variant_path = prepared_root / identity
    if not variant_path.is_file():
        raise FileNotFoundError(
            f"prepared public Mermaid {theme} variant not found: {variant_path}"
        )
    source_bytes = variant_path.read_bytes()
    try:
        sanitized = sanitize_svg_bytes(source_bytes)
    except ValueError as exc:
        raise RuntimeError(
            f"prepared public Mermaid {theme} variant is not safe: {projection_id}"
        ) from exc
    if sanitized.bytes != source_bytes:
        raise RuntimeError(
            f"prepared public Mermaid {theme} variant is not the verified sanitized bytes: "
            f"{projection_id}"
        )
    rendered = inspect_sanitized_mermaid_svg(f"{projection_id}/{theme}", source_bytes)
    if (
        rendered.title != str(record["title"])
        or rendered.description != str(record["description"])
    ):
        raise RuntimeError(
            f"prepared public Mermaid {theme} variant metadata does not match its manifest: "
            f"{projection_id}"
        )
    return rendered


def _validate_pair_geometry(
    record: Mapping[str, Any],
    rendered_by_theme: Mapping[str, RenderedMermaidSvg],
) -> None:
    light = rendered_by_theme["light"].view_box
    dark = rendered_by_theme["dark"].view_box
    light_ratio = light[2] / light[3]
    dark_ratio = dark[2] / dark[3]
    if not math.isclose(light_ratio, dark_ratio, rel_tol=1e-9, abs_tol=1e-9):
        raise RuntimeError(
            "prepared public Mermaid variants have incompatible responsive geometry: "
            f"{record['projection_id']}"
        )


def load_prepared_public_mermaid_projection(
    working_root: Path,
    *,
    scope: str,
) -> PreparedPublicMermaidProjection:
    """Load and revalidate the manifest-owned prepared pairs without writing."""

    prepared_root = working_root / PUBLIC_MERMAID_PREPARED_RELATIVE_PATH
    manifest_path = prepared_root / PUBLIC_MERMAID_MANIFEST_FILENAME
    if not manifest_path.exists():
        return PreparedPublicMermaidProjection({}, {}, frozenset())
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"prepared public Mermaid manifest must be valid UTF-8 JSON: {manifest_path}"
        ) from exc
    if not isinstance(manifest, Mapping):
        raise ValueError("prepared public Mermaid manifest must be a JSON object")

    records = validate_public_mermaid_manifest(manifest, scope=scope)
    records_by_doc_id: dict[str, list[dict[str, Any]]] = {}
    variant_bytes_by_projection_id: dict[str, dict[str, bytes]] = {}
    for record in records:
        rendered_by_theme = {
            theme: _validated_variant(prepared_root, record, theme)
            for theme in PUBLIC_MERMAID_THEMES
        }
        _validate_pair_geometry(record, rendered_by_theme)
        records_by_doc_id.setdefault(record["doc_id"], []).append(record)
        variant_bytes_by_projection_id[record["projection_id"]] = {
            theme: rendered_by_theme[theme].bytes
            for theme in PUBLIC_MERMAID_THEMES
        }

    normalized_records = {
        doc_id: tuple(sorted(doc_records, key=lambda item: item["fence_index"]))
        for doc_id, doc_records in records_by_doc_id.items()
    }
    return PreparedPublicMermaidProjection(
        records_by_doc_id=normalized_records,
        variant_bytes_by_projection_id=variant_bytes_by_projection_id,
        projection_ids=frozenset(variant_bytes_by_projection_id),
    )


def _diagram_html(record: Mapping[str, Any]) -> str:
    projection_id = html.escape(str(record["projection_id"]), quote=True)
    title = html.escape(str(record["title"]), quote=True)
    description = html.escape(str(record["description"]), quote=True)
    light_url = html.escape(str(record["variants"]["light"]["url"]), quote=True)
    dark_url = html.escape(str(record["variants"]["dark"]["url"]), quote=True)
    description_id = f"{projection_id}--description"
    return (
        f'<img hidden data-docs-viewer-diagram-kind="themed-mermaid" '
        f'data-docs-viewer-diagram-light-src="{light_url}" '
        f'data-docs-viewer-diagram-dark-src="{dark_url}" '
        f'alt="{title}" title="{title}" aria-describedby="{description_id}">'
        f'<span class="visually-hidden" id="{description_id}">{description}</span>'
    )


def project_public_mermaid_payload(
    payload: Any,
    *,
    doc_id: str,
    records: tuple[dict[str, Any], ...],
) -> tuple[Any, frozenset[str]]:
    """Replace every rendered Mermaid fence with its verified public pair contract."""

    if not isinstance(payload, Mapping):
        if records:
            raise ValueError(
                f"public Mermaid manifest references a non-object document payload: {doc_id}"
            )
        return payload, frozenset()
    content_html = payload.get("content_html")
    if not isinstance(content_html, str):
        if records:
            raise ValueError(
                f"public Mermaid manifest references a payload without content_html: {doc_id}"
            )
        return payload, frozenset()

    matches = list(PUBLIC_MERMAID_HTML_FENCE_PATTERN.finditer(content_html))
    records_by_fence_index = {record["fence_index"]: record for record in records}
    if len(records_by_fence_index) != len(records):
        raise ValueError(f"public Mermaid manifest has duplicate fence ordinals for {doc_id}")
    if set(records_by_fence_index) != set(range(1, len(matches) + 1)):
        raise RuntimeError(
            f"public Mermaid projection is incomplete or stale for document {doc_id}"
        )

    used_projection_ids: set[str] = set()

    def replacement(match: re.Match[str]) -> str:
        fence_index = len(used_projection_ids) + 1
        record = records_by_fence_index[fence_index]
        source = html.unescape(match.group("source"))
        if _source_digest(source) != record["source_digest"]:
            raise RuntimeError(
                f"public Mermaid projection source digest is stale for "
                f"{record['projection_id']}"
            )
        used_projection_ids.add(record["projection_id"])
        return _diagram_html(record)

    projected_html = PUBLIC_MERMAID_HTML_FENCE_PATTERN.sub(replacement, content_html)
    return {**payload, "content_html": projected_html}, frozenset(used_projection_ids)


def public_mermaid_payload_requires_projection(payload: Any) -> bool:
    if not isinstance(payload, Mapping):
        return False
    content_html = payload.get("content_html")
    return isinstance(content_html, str) and bool(
        PUBLIC_MERMAID_HTML_FENCE_PATTERN.search(content_html)
    )


def public_mermaid_variant_files(
    projection: PreparedPublicMermaidProjection,
    *,
    used_projection_ids: frozenset[str],
) -> dict[Path, bytes]:
    """Return exact prepared variant bytes only after every manifest record was consumed."""

    if used_projection_ids != projection.projection_ids:
        missing = sorted(projection.projection_ids - used_projection_ids)
        unexpected = sorted(used_projection_ids - projection.projection_ids)
        detail = []
        if missing:
            detail.append("unused manifest records: " + ", ".join(missing))
        if unexpected:
            detail.append("unowned projected records: " + ", ".join(unexpected))
        raise RuntimeError("public Mermaid projection manifest is stale; " + "; ".join(detail))

    files: dict[Path, bytes] = {}
    for doc_records in projection.records_by_doc_id.values():
        for record in doc_records:
            projection_id = record["projection_id"]
            for theme in PUBLIC_MERMAID_THEMES:
                identity = Path(record["variants"][theme]["artifact_identity"])
                files[identity] = projection.variant_bytes_by_projection_id[projection_id][theme]
    return files


__all__ = [
    "PUBLIC_MERMAID_HTML_FENCE_PATTERN",
    "PUBLIC_MERMAID_MANIFEST_FILENAME",
    "PUBLIC_MERMAID_PREPARED_RELATIVE_PATH",
    "PreparedPublicMermaidProjection",
    "load_prepared_public_mermaid_projection",
    "project_public_mermaid_payload",
    "public_mermaid_payload_requires_projection",
    "public_mermaid_variant_files",
]

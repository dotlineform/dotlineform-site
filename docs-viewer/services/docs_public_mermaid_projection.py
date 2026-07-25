#!/usr/bin/env python3
"""Pure planning for public light/dark projections of inline Mermaid fences."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from markdown_it import MarkdownIt

from docs_artifact_locations import normalize_artifact_identity
from docs_document_identity import is_immutable_doc_id
from docs_mermaid_accessibility import mermaid_accessibility_metadata


PUBLIC_MERMAID_PLAN_SCHEMA_VERSION = "docs_public_mermaid_projection_plan_v1"
PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION = "docs_public_mermaid_projection_manifest_v1"
PUBLIC_MERMAID_DIAGRAM_SCHEMA_VERSION = "docs_public_mermaid_diagram_v1"
PUBLIC_MERMAID_ASSET_PREFIX = Path("projection-assets/mermaid")
PUBLIC_MERMAID_THEMES = ("light", "dark")
SOURCE_DIGEST_PATTERN = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class PublicMermaidFence:
    doc_id: str
    fence_index: int
    source_line: int
    source_text: str
    source_digest: str
    title: str
    description: str

    @property
    def projection_id(self) -> str:
        return public_mermaid_projection_id(self.doc_id, self.fence_index)


@dataclass(frozen=True)
class PublicMermaidFenceFailure:
    doc_id: str
    fence_index: int
    source_line: int
    projection_id: str
    message: str


def public_mermaid_projection_id(doc_id: str, fence_index: int) -> str:
    """Return one stable identity for a Mermaid fence's document-local ordinal."""

    normalized_doc_id = str(doc_id or "").strip()
    if not is_immutable_doc_id(normalized_doc_id):
        raise ValueError(f"public Mermaid projection requires an immutable doc_id: {normalized_doc_id!r}")
    if not isinstance(fence_index, int) or isinstance(fence_index, bool) or fence_index < 1:
        raise ValueError("public Mermaid fence_index must be a positive integer")
    return f"{normalized_doc_id}--mermaid-{fence_index:04d}"


def public_mermaid_variant_identity(projection_id: str, theme: str) -> str:
    normalized_theme = str(theme or "").strip().lower()
    if normalized_theme not in PUBLIC_MERMAID_THEMES:
        raise ValueError(f"public Mermaid theme must be one of: {', '.join(PUBLIC_MERMAID_THEMES)}")
    return normalize_artifact_identity(PUBLIC_MERMAID_ASSET_PREFIX / projection_id / f"{normalized_theme}.svg")


def _source_digest(source: str) -> str:
    return f"sha256:{hashlib.sha256(source.encode('utf-8')).hexdigest()}"


def _is_mermaid_fence(token: Any) -> bool:
    if getattr(token, "type", "") != "fence":
        return False
    info = str(getattr(token, "info", "") or "").strip()
    return bool(info) and info.split(maxsplit=1)[0].lower() == "mermaid"


def inventory_public_mermaid_fences(
    documents: Iterable[tuple[str, str]],
) -> tuple[tuple[PublicMermaidFence, ...], tuple[PublicMermaidFenceFailure, ...]]:
    """Inventory accessible Mermaid fences without changing canonical Markdown."""

    normalized_documents: list[tuple[str, str]] = []
    seen_doc_ids: set[str] = set()
    for raw_doc_id, raw_markdown in documents:
        doc_id = str(raw_doc_id or "").strip()
        public_mermaid_projection_id(doc_id, 1)
        if doc_id in seen_doc_ids:
            raise ValueError(f"duplicate document in public Mermaid projection inventory: {doc_id}")
        seen_doc_ids.add(doc_id)
        normalized_documents.append((doc_id, str(raw_markdown or "")))

    fences: list[PublicMermaidFence] = []
    failures: list[PublicMermaidFenceFailure] = []
    renderer = MarkdownIt("commonmark")
    for doc_id, markdown in sorted(normalized_documents):
        fence_index = 0
        for token in renderer.parse(markdown):
            if not _is_mermaid_fence(token):
                continue
            fence_index += 1
            source_line = int(token.map[0]) + 1 if token.map else 1
            projection_id = public_mermaid_projection_id(doc_id, fence_index)
            source_text = str(token.content or "")
            try:
                accessibility = mermaid_accessibility_metadata(projection_id, source_text)
            except ValueError as exc:
                failures.append(
                    PublicMermaidFenceFailure(
                        doc_id=doc_id,
                        fence_index=fence_index,
                        source_line=source_line,
                        projection_id=projection_id,
                        message=str(exc),
                    )
                )
                continue
            fences.append(
                PublicMermaidFence(
                    doc_id=doc_id,
                    fence_index=fence_index,
                    source_line=source_line,
                    source_text=source_text,
                    source_digest=_source_digest(source_text),
                    title=accessibility.title,
                    description=accessibility.description,
                )
            )
    return tuple(fences), tuple(failures)


def _public_url_prefix(value: str) -> str:
    prefix = str(value or "").strip().rstrip("/")
    if not prefix.startswith("/") or "?" in prefix or "#" in prefix:
        raise ValueError("public Mermaid projection URL prefix must be an absolute browser path")
    return prefix


def _variant_record(projection_id: str, theme: str, public_url_prefix: str) -> dict[str, str]:
    artifact_identity = public_mermaid_variant_identity(projection_id, theme)
    return {
        "artifact_identity": artifact_identity,
        "url": f"{public_url_prefix}/{artifact_identity}",
    }


def _projection_record(fence: PublicMermaidFence, public_url_prefix: str) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_MERMAID_DIAGRAM_SCHEMA_VERSION,
        "kind": "themed-mermaid",
        "projection_id": fence.projection_id,
        "doc_id": fence.doc_id,
        "fence_index": fence.fence_index,
        "alt": fence.title,
        "title": fence.title,
        "description": fence.description,
        "variants": {
            theme: _variant_record(fence.projection_id, theme, public_url_prefix)
            for theme in PUBLIC_MERMAID_THEMES
        },
    }


def _manifest_record(fence: PublicMermaidFence, projection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "projection_id": fence.projection_id,
        "doc_id": fence.doc_id,
        "fence_index": fence.fence_index,
        "source_digest": fence.source_digest,
        "title": fence.title,
        "description": fence.description,
        "variants": {
            theme: dict(projection["variants"][theme])
            for theme in PUBLIC_MERMAID_THEMES
        },
    }


def _validated_previous_records(
    previous_manifest: Mapping[str, Any] | None,
    *,
    scope: str,
) -> tuple[dict[str, Any], ...]:
    if previous_manifest is None:
        return ()
    if previous_manifest.get("schema_version") != PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            "public Mermaid projection manifest schema_version must be "
            f"{PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION}"
        )
    if str(previous_manifest.get("scope") or "").strip() != scope:
        raise ValueError("public Mermaid projection manifest scope does not match the requested scope")
    raw_records = previous_manifest.get("diagrams")
    if not isinstance(raw_records, list):
        raise ValueError("public Mermaid projection manifest diagrams must be a list")

    records: list[dict[str, Any]] = []
    seen_projection_ids: set[str] = set()
    for raw_record in raw_records:
        if not isinstance(raw_record, Mapping):
            raise ValueError("public Mermaid projection manifest diagram must be an object")
        doc_id = str(raw_record.get("doc_id") or "").strip()
        fence_index = raw_record.get("fence_index")
        expected_projection_id = public_mermaid_projection_id(doc_id, fence_index)
        projection_id = str(raw_record.get("projection_id") or "").strip()
        if projection_id != expected_projection_id:
            raise ValueError("public Mermaid projection manifest has an invalid projection_id")
        if projection_id in seen_projection_ids:
            raise ValueError("public Mermaid projection manifest has duplicate projection identities")
        seen_projection_ids.add(projection_id)
        source_digest = str(raw_record.get("source_digest") or "").strip()
        if not SOURCE_DIGEST_PATTERN.fullmatch(source_digest):
            raise ValueError("public Mermaid projection manifest has an invalid source_digest")
        title = str(raw_record.get("title") or "").strip()
        description = str(raw_record.get("description") or "").strip()
        if not title or not description:
            raise ValueError("public Mermaid projection manifest requires title and description")
        variants = raw_record.get("variants")
        if not isinstance(variants, Mapping) or set(variants) != set(PUBLIC_MERMAID_THEMES):
            raise ValueError("public Mermaid projection manifest requires explicit light and dark variants")
        normalized_variants: dict[str, dict[str, str]] = {}
        for theme in PUBLIC_MERMAID_THEMES:
            variant = variants[theme]
            if not isinstance(variant, Mapping):
                raise ValueError("public Mermaid projection manifest variant must be an object")
            expected_identity = public_mermaid_variant_identity(projection_id, theme)
            identity = normalize_artifact_identity(str(variant.get("artifact_identity") or ""))
            if identity != expected_identity:
                raise ValueError("public Mermaid projection manifest variant is outside manifest ownership")
            url = str(variant.get("url") or "").strip()
            if not url.startswith("/") or not url.endswith(f"/{identity}"):
                raise ValueError("public Mermaid projection manifest variant has an invalid URL")
            normalized_variants[theme] = {
                "artifact_identity": identity,
                "url": url,
            }
        records.append(
            {
                "projection_id": projection_id,
                "doc_id": doc_id,
                "fence_index": fence_index,
                "source_digest": source_digest,
                "title": title,
                "description": description,
                "variants": normalized_variants,
            }
        )
    return tuple(sorted(records, key=lambda item: item["projection_id"]))


def plan_public_mermaid_projection(
    *,
    scope: str,
    documents: Iterable[tuple[str, str]],
    public_url_prefix: str,
    previous_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a complete no-write plan, next manifest, failures, and stale pairs."""

    normalized_scope = str(scope or "").strip().lower()
    if not normalized_scope:
        raise ValueError("public Mermaid projection scope is required")
    url_prefix = _public_url_prefix(public_url_prefix)
    fences, failures = inventory_public_mermaid_fences(documents)
    previous_records = _validated_previous_records(previous_manifest, scope=normalized_scope)
    previous_by_id = {record["projection_id"]: record for record in previous_records}

    diagrams: list[dict[str, Any]] = []
    manifest_records: list[dict[str, Any]] = []
    for fence in fences:
        projection = _projection_record(fence, url_prefix)
        manifest_record = _manifest_record(fence, projection)
        previous_record = previous_by_id.get(fence.projection_id)
        action = (
            "create"
            if previous_record is None
            else "unchanged"
            if previous_record == manifest_record
            else "replace"
        )
        diagrams.append(
            {
                "action": action,
                "source": {
                    "doc_id": fence.doc_id,
                    "fence_index": fence.fence_index,
                    "source_line": fence.source_line,
                    "source_digest": fence.source_digest,
                    "mermaid": fence.source_text,
                },
                "projection": projection,
            }
        )
        manifest_records.append(manifest_record)

    desired_ids = {record["projection_id"] for record in manifest_records}
    removals = [
        {
            "projection_id": record["projection_id"],
            "doc_id": record["doc_id"],
            "fence_index": record["fence_index"],
            "variant_identities": [
                record["variants"][theme]["artifact_identity"]
                for theme in PUBLIC_MERMAID_THEMES
            ],
        }
        for record in previous_records
        if record["projection_id"] not in desired_ids
    ]
    failure_records = [
        {
            "doc_id": failure.doc_id,
            "fence_index": failure.fence_index,
            "source_line": failure.source_line,
            "projection_id": failure.projection_id,
            "message": failure.message,
        }
        for failure in failures
    ]
    manifest = {
        "schema_version": PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION,
        "scope": normalized_scope,
        "diagrams": manifest_records,
    }
    return {
        "schema_version": PUBLIC_MERMAID_PLAN_SCHEMA_VERSION,
        "mode": "dry-run",
        "scope": normalized_scope,
        "summary": {
            "diagram_count": len(diagrams),
            "variant_count": len(diagrams) * len(PUBLIC_MERMAID_THEMES),
            "create_count": sum(item["action"] == "create" for item in diagrams),
            "replace_count": sum(item["action"] == "replace" for item in diagrams),
            "unchanged_count": sum(item["action"] == "unchanged" for item in diagrams),
            "failure_count": len(failure_records),
            "removal_family_count": len(removals),
            "removal_variant_count": sum(len(item["variant_identities"]) for item in removals),
        },
        "diagrams": diagrams,
        "failures": failure_records,
        "removals": removals,
        "manifest": manifest,
    }


def public_mermaid_projection_report(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Return diagnostics without embedding canonical Mermaid source text."""

    return {
        "schema_version": plan["schema_version"],
        "mode": plan["mode"],
        "scope": plan["scope"],
        "summary": dict(plan["summary"]),
        "diagrams": [
            {
                "action": item["action"],
                "source": {
                    key: value
                    for key, value in item["source"].items()
                    if key != "mermaid"
                },
                "projection": item["projection"],
            }
            for item in plan["diagrams"]
        ],
        "failures": list(plan["failures"]),
        "removals": list(plan["removals"]),
        "manifest": plan["manifest"],
    }


__all__ = [
    "PUBLIC_MERMAID_ASSET_PREFIX",
    "PUBLIC_MERMAID_DIAGRAM_SCHEMA_VERSION",
    "PUBLIC_MERMAID_MANIFEST_SCHEMA_VERSION",
    "PUBLIC_MERMAID_PLAN_SCHEMA_VERSION",
    "PUBLIC_MERMAID_THEMES",
    "PublicMermaidFence",
    "PublicMermaidFenceFailure",
    "inventory_public_mermaid_fences",
    "plan_public_mermaid_projection",
    "public_mermaid_projection_id",
    "public_mermaid_projection_report",
    "public_mermaid_variant_identity",
]

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote


SEMANTIC_REFERENCE_REGISTRY_SCHEMA_VERSION = "docs_semantic_reference_registry_v1"
SEMANTIC_REFERENCE_REGISTRY_PATH = Path("docs-viewer/config/semantic-references/registry.json")
SUPPORTED_NORMALIZERS = {"digits_left_pad", "series_id_or_slug", "slug"}


@dataclass(frozen=True)
class SemanticReferenceIdPolicy:
    normalizer: str
    width: int | None
    input_pattern: str
    canonical_pattern: str
    example: str


@dataclass(frozen=True)
class SemanticReferenceRoute:
    type: str
    path: str
    param: str


@dataclass(frozen=True)
class SemanticReferenceKind:
    kind: str
    id: SemanticReferenceIdPolicy
    route: SemanticReferenceRoute
    source_editor: dict[str, Any]
    order: int


@dataclass(frozen=True)
class SemanticReferenceRegistry:
    schema_version: str
    target_lookup_url: str
    kinds: tuple[SemanticReferenceKind, ...]

    def kind(self, kind: str) -> SemanticReferenceKind | None:
        normalized = str(kind or "").strip().lower()
        for record in self.kinds:
            if record.kind == normalized:
                return record
        return None

    @property
    def supported_kinds(self) -> set[str]:
        return {record.kind for record in self.kinds}


def load_semantic_reference_registry(repo_root: Path) -> SemanticReferenceRegistry | None:
    path = repo_root / SEMANTIC_REFERENCE_REGISTRY_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parse_semantic_reference_registry(payload)


def parse_semantic_reference_registry(payload: Any) -> SemanticReferenceRegistry | None:
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != SEMANTIC_REFERENCE_REGISTRY_SCHEMA_VERSION:
        return None
    target_lookup_url = str(payload.get("target_lookup_url") or "").strip()
    if not target_lookup_url.startswith("/"):
        return None
    raw_kinds = payload.get("kinds")
    if not isinstance(raw_kinds, list):
        return None
    kinds: list[SemanticReferenceKind] = []
    seen: set[str] = set()
    for index, raw_kind in enumerate(raw_kinds):
        record = parse_semantic_reference_kind(raw_kind, index)
        if record is None or record.kind in seen:
            return None
        seen.add(record.kind)
        kinds.append(record)
    return SemanticReferenceRegistry(
        schema_version=SEMANTIC_REFERENCE_REGISTRY_SCHEMA_VERSION,
        target_lookup_url=target_lookup_url,
        kinds=tuple(kinds),
    )


def parse_semantic_reference_kind(payload: Any, order: int) -> SemanticReferenceKind | None:
    if not isinstance(payload, dict):
        return None
    kind = str(payload.get("kind") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]+", kind):
        return None
    id_policy = parse_id_policy(payload.get("id"))
    route = parse_route(payload.get("route"))
    source_editor = payload.get("source_editor")
    if id_policy is None or route is None or not isinstance(source_editor, dict):
        return None
    return SemanticReferenceKind(
        kind=kind,
        id=id_policy,
        route=route,
        source_editor=dict(source_editor),
        order=order,
    )


def parse_id_policy(payload: Any) -> SemanticReferenceIdPolicy | None:
    if not isinstance(payload, dict):
        return None
    normalizer = str(payload.get("normalizer") or "").strip()
    if normalizer not in SUPPORTED_NORMALIZERS:
        return None
    width = payload.get("width")
    parsed_width = int(width) if isinstance(width, int) and width > 0 else None
    return SemanticReferenceIdPolicy(
        normalizer=normalizer,
        width=parsed_width,
        input_pattern=str(payload.get("input_pattern") or "").strip(),
        canonical_pattern=str(payload.get("canonical_pattern") or "").strip(),
        example=str(payload.get("example") or "").strip(),
    )


def parse_route(payload: Any) -> SemanticReferenceRoute | None:
    if not isinstance(payload, dict):
        return None
    route_type = str(payload.get("type") or "").strip()
    path = str(payload.get("path") or "").strip()
    param = str(payload.get("param") or "").strip()
    if route_type != "query" or not path.startswith("/") or not param:
        return None
    return SemanticReferenceRoute(type=route_type, path=path, param=param)


def normalize_semantic_reference_id(value: str, policy: SemanticReferenceIdPolicy) -> str | None:
    if policy.normalizer == "digits_left_pad":
        return normalize_digits_left_pad(value, policy.width or 0)
    if policy.normalizer == "series_id_or_slug":
        return normalize_series_id_or_slug(value, policy.width or 3)
    if policy.normalizer == "slug":
        return normalize_slug(value)
    return None


def normalize_digits_left_pad(value: str, width: int) -> str | None:
    text = re.sub(r"\D", "", str(value or "").strip().removeprefix("'"))
    if not text or (width and len(text) > width):
        return None
    return text.rjust(width, "0") if width else text


def normalize_series_id_or_slug(value: str, width: int) -> str | None:
    text = re.sub(r"\.0+\Z", "", str(value or "").strip().lower().removeprefix("'"))
    if not text:
        return None
    if re.fullmatch(r"\d+", text):
        return text.rjust(width, "0") if width else text
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
        return text
    return None


def normalize_slug(value: str) -> str | None:
    text = str(value or "").strip().lower().removesuffix(".md")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
        return None
    return text


def semantic_reference_href(kind: SemanticReferenceKind, target_id: str) -> str:
    if kind.route.type == "query":
        separator = "&" if "?" in kind.route.path else "?"
        return f"{kind.route.path}{separator}{quote(kind.route.param)}={quote(str(target_id))}"
    return kind.route.path

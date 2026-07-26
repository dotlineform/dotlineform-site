from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any


SEMANTIC_TOKEN_REGISTRY_SCHEMA_VERSION = "docs_semantic_token_registry_v1"
SEMANTIC_TOKEN_FAMILY_SCHEMA_VERSION = "docs_semantic_token_family_definition_v1"
SEMANTIC_TOKEN_REGISTRY_PATH = Path("docs-viewer/config/semantic-tokens/registry.json")
SUPPORTED_NORMALIZERS = {"digits_left_pad", "series_id_or_slug", "slug"}


@dataclass(frozen=True)
class SemanticTokenIdPolicy:
    normalizer: str
    width: int | None
    input_pattern: str
    canonical_pattern: str


@dataclass(frozen=True)
class SemanticTokenTargetType:
    key: str
    label: str
    id_policy: SemanticTokenIdPolicy
    lookup_adapter: str
    lookup_fields: tuple[str, ...]
    order: int


@dataclass(frozen=True)
class SemanticTokenFamily:
    key: str
    labels: dict[str, str]
    occurrence_fields: tuple[dict[str, Any], ...]
    ui_contributions: dict[str, str]
    target_types: tuple[SemanticTokenTargetType, ...]
    order: int

    def target_type(self, key: str) -> SemanticTokenTargetType | None:
        normalized = str(key or "").strip().lower()
        for record in self.target_types:
            if record.key == normalized:
                return record
        return None


@dataclass(frozen=True)
class SemanticTokenRegistry:
    target_lookup_url: str
    families: tuple[SemanticTokenFamily, ...]

    def family(self, key: str) -> SemanticTokenFamily | None:
        normalized = str(key or "").strip().lower()
        for record in self.families:
            if record.key == normalized:
                return record
        return None


def load_semantic_token_registry(repo_root: Path) -> SemanticTokenRegistry | None:
    try:
        payload = json.loads((repo_root / SEMANTIC_TOKEN_REGISTRY_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parse_semantic_token_registry(payload)


def parse_semantic_token_registry(payload: Any) -> SemanticTokenRegistry | None:
    if not isinstance(payload, dict) or payload.get("schema_version") != SEMANTIC_TOKEN_REGISTRY_SCHEMA_VERSION:
        return None
    target_lookup_url = str(payload.get("target_lookup_url") or "").strip()
    raw_families = payload.get("families")
    if not target_lookup_url.startswith("/") or not isinstance(raw_families, list):
        return None
    families: list[SemanticTokenFamily] = []
    seen: set[str] = set()
    for index, raw_family in enumerate(raw_families):
        family = parse_semantic_token_family(raw_family, index)
        if family is None or family.key in seen:
            return None
        seen.add(family.key)
        families.append(family)
    return SemanticTokenRegistry(target_lookup_url=target_lookup_url, families=tuple(families))


def parse_semantic_token_family(payload: Any, order: int) -> SemanticTokenFamily | None:
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != SEMANTIC_TOKEN_FAMILY_SCHEMA_VERSION
    ):
        return None
    key = str(payload.get("key") or "").strip().lower()
    labels = payload.get("labels")
    occurrence_fields = payload.get("occurrence_fields")
    ui_contributions = payload.get("ui_contributions")
    raw_target_types = payload.get("target_types")
    if (
        not re.fullmatch(r"[a-z][a-z0-9-]*", key)
        or not isinstance(labels, dict)
        or not isinstance(occurrence_fields, list)
        or not isinstance(ui_contributions, dict)
        or not isinstance(raw_target_types, list)
    ):
        return None
    target_types: list[SemanticTokenTargetType] = []
    seen: set[str] = set()
    for index, raw_target_type in enumerate(raw_target_types):
        target_type = parse_semantic_token_target_type(raw_target_type, index)
        if target_type is None or target_type.key in seen:
            return None
        seen.add(target_type.key)
        target_types.append(target_type)
    return SemanticTokenFamily(
        key=key,
        labels={str(name): str(value) for name, value in labels.items()},
        occurrence_fields=tuple(dict(field) for field in occurrence_fields if isinstance(field, dict)),
        ui_contributions={str(name): str(value) for name, value in ui_contributions.items()},
        target_types=tuple(target_types),
        order=order,
    )


def parse_semantic_token_target_type(payload: Any, order: int) -> SemanticTokenTargetType | None:
    if not isinstance(payload, dict):
        return None
    key = str(payload.get("key") or "").strip().lower()
    label = str(payload.get("label") or "").strip()
    lookup_adapter = str(payload.get("lookup_adapter") or "").strip()
    lookup_fields = payload.get("lookup_fields")
    id_policy = parse_semantic_token_id_policy(payload.get("id_policy"))
    if (
        not re.fullmatch(r"[a-z][a-z0-9-]*", key)
        or not label
        or not lookup_adapter
        or not isinstance(lookup_fields, list)
        or id_policy is None
    ):
        return None
    fields = tuple(str(field).strip() for field in lookup_fields if str(field).strip())
    if not {"title", "href"}.issubset(fields):
        return None
    return SemanticTokenTargetType(
        key=key,
        label=label,
        id_policy=id_policy,
        lookup_adapter=lookup_adapter,
        lookup_fields=fields,
        order=order,
    )


def parse_semantic_token_id_policy(payload: Any) -> SemanticTokenIdPolicy | None:
    if not isinstance(payload, dict):
        return None
    normalizer = str(payload.get("normalizer") or "").strip()
    input_pattern = str(payload.get("input_pattern") or "").strip()
    canonical_pattern = str(payload.get("canonical_pattern") or "").strip()
    width = payload.get("width")
    parsed_width = width if isinstance(width, int) and width > 0 else None
    if normalizer not in SUPPORTED_NORMALIZERS or not input_pattern or not canonical_pattern:
        return None
    try:
        re.compile(input_pattern)
        re.compile(canonical_pattern)
    except re.error:
        return None
    return SemanticTokenIdPolicy(
        normalizer=normalizer,
        width=parsed_width,
        input_pattern=input_pattern,
        canonical_pattern=canonical_pattern,
    )


def normalize_semantic_token_id(value: str, policy: SemanticTokenIdPolicy) -> str | None:
    text = str(value or "").strip()
    if not re.fullmatch(policy.input_pattern, text):
        return None
    if policy.normalizer == "digits_left_pad":
        normalized = text.rjust(policy.width or 0, "0")
    elif policy.normalizer in {"series_id_or_slug", "slug"}:
        normalized = text.lower()
    else:
        return None
    return normalized if re.fullmatch(policy.canonical_pattern, normalized) else None

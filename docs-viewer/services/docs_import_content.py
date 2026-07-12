#!/usr/bin/env python3
"""Generic normalized content records for Docs Import adapters."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


CONTENT_INTENT_REPLACE = "replace"
CONTENT_INTENT_PRESERVE_EXISTING = "preserve-existing"
CONTENT_INTENT_EMPTY_NEW = "empty-new"
CONTENT_INTENTS = {
    CONTENT_INTENT_REPLACE,
    CONTENT_INTENT_PRESERVE_EXISTING,
    CONTENT_INTENT_EMPTY_NEW,
}

CONTENT_FORMAT_MARKDOWN = "markdown"
CONTENT_FORMAT_HTML = "html"
CONTENT_FORMAT_PLAIN_TEXT = "plain_text"
CONTENT_FORMATS = {
    CONTENT_FORMAT_MARKDOWN,
    CONTENT_FORMAT_HTML,
    CONTENT_FORMAT_PLAIN_TEXT,
}


def normalized_text(value: Any) -> str:
    return str(value or "").strip()


@dataclass(frozen=True)
class ImportContent:
    """Wrapper-neutral input for one planned Docs Import document."""

    source_kind: str
    source_identity: str
    record_identity: str
    doc_id: str
    title: str
    content_intent: str
    content_format: str
    content: str | None = None
    front_matter: dict[str, Any] = field(default_factory=dict)
    parent_id: str = ""
    links: tuple[dict[str, Any], ...] = ()
    assets: tuple[dict[str, Any], ...] = ()
    diagnostics: tuple[dict[str, Any], ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for field_name in ("source_kind", "source_identity", "record_identity", "doc_id", "title"):
            if not normalized_text(getattr(self, field_name)):
                raise ValueError(f"ImportContent {field_name} is required")
        if self.content_intent not in CONTENT_INTENTS:
            raise ValueError(
                "ImportContent content_intent must be one of: "
                + ", ".join(sorted(CONTENT_INTENTS))
            )
        if self.content_format not in CONTENT_FORMATS:
            raise ValueError(
                "ImportContent content_format must be one of: "
                + ", ".join(sorted(CONTENT_FORMATS))
            )
        if self.content_intent == CONTENT_INTENT_REPLACE:
            if not isinstance(self.content, str):
                raise ValueError("ImportContent replace intent requires string content")
        elif self.content is not None:
            raise ValueError(
                f"ImportContent {self.content_intent} intent must not carry replacement content"
            )
        if not isinstance(self.front_matter, dict):
            raise ValueError("ImportContent front_matter must be an object")
        for field_name in ("links", "assets", "diagnostics"):
            values = getattr(self, field_name)
            if not isinstance(values, tuple) or any(not isinstance(item, dict) for item in values):
                raise ValueError(f"ImportContent {field_name} must be a tuple of objects")
        if not isinstance(self.provenance, dict):
            raise ValueError("ImportContent provenance must be an object")

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_kind": self.source_kind,
            "source_identity": self.source_identity,
            "record_identity": self.record_identity,
            "doc_id": self.doc_id,
            "title": self.title,
            "content_intent": self.content_intent,
            "content_format": self.content_format,
            "content": self.content,
            "front_matter": copy.deepcopy(self.front_matter),
            "parent_id": self.parent_id,
            "links": copy.deepcopy(list(self.links)),
            "assets": copy.deepcopy(list(self.assets)),
            "diagnostics": copy.deepcopy(list(self.diagnostics)),
            "provenance": copy.deepcopy(self.provenance),
        }


__all__ = [
    "CONTENT_FORMATS",
    "CONTENT_FORMAT_HTML",
    "CONTENT_FORMAT_MARKDOWN",
    "CONTENT_FORMAT_PLAIN_TEXT",
    "CONTENT_INTENTS",
    "CONTENT_INTENT_EMPTY_NEW",
    "CONTENT_INTENT_PRESERVE_EXISTING",
    "CONTENT_INTENT_REPLACE",
    "ImportContent",
]

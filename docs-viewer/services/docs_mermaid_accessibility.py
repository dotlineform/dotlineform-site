#!/usr/bin/env python3
"""Shared accessibility metadata parsing for canonical Mermaid source."""

from __future__ import annotations

from dataclasses import dataclass
import re


ACC_TITLE_PATTERN = re.compile(r"^\s*accTitle\s*:\s*(\S.*)\s*$", re.MULTILINE)
ACC_DESCR_INLINE_PATTERN = re.compile(r"^\s*accDescr\s*:\s*(\S.*)\s*$", re.MULTILINE)
ACC_DESCR_BLOCK_PATTERN = re.compile(r"^\s*accDescr\s*\{\s*(.*?)\s*\}", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class MermaidAccessibility:
    title: str
    description: str


def _normalized_metadata(value: str) -> str:
    return " ".join(str(value or "").split())


def mermaid_accessibility_metadata(identity: str, source: str) -> MermaidAccessibility:
    """Return the required Mermaid title and description or fail explicitly."""

    title_match = ACC_TITLE_PATTERN.search(source)
    if title_match is None or not _normalized_metadata(title_match.group(1)):
        raise ValueError(f"Mermaid source {identity!r} requires a non-empty accTitle")

    description_match = (
        ACC_DESCR_INLINE_PATTERN.search(source)
        or ACC_DESCR_BLOCK_PATTERN.search(source)
    )
    if description_match is None or not _normalized_metadata(description_match.group(1)):
        raise ValueError(f"Mermaid source {identity!r} requires a non-empty accDescr")

    return MermaidAccessibility(
        title=_normalized_metadata(title_match.group(1)),
        description=_normalized_metadata(description_match.group(1)),
    )


__all__ = [
    "ACC_DESCR_BLOCK_PATTERN",
    "ACC_DESCR_INLINE_PATTERN",
    "ACC_TITLE_PATTERN",
    "MermaidAccessibility",
    "mermaid_accessibility_metadata",
]

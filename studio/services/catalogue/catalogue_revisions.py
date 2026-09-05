"""Revision checks for exact canonical Catalogue records."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


class CatalogueRevisionConflict(ValueError):
    """The source record changed after the editor loaded it."""


def record_hash(record: Mapping[str, Any]) -> str:
    """Return an opaque revision supplied by read and save responses."""
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def require_record_revision(record: Mapping[str, Any], expected: Any) -> None:
    """Reject a missing revision or stale edit before any source write."""
    if not isinstance(expected, str) or not expected:
        raise ValueError("expected_record_hash is required")
    if record_hash(record) != expected:
        raise CatalogueRevisionConflict("Catalogue record changed; reload before saving or deleting.")

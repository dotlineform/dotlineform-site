"""Deterministic canonical Work record hashes for editor responses."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def record_hash(record: Mapping[str, Any]) -> str:
    """Return the opaque Work hash supplied by read and save responses."""
    encoded = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

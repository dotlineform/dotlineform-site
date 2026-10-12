"""Shared pure helpers for catalogue generation payloads."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, Optional


def normalize_text(value: Any) -> str:
    """Normalize source text by trimming and stripping a leading apostrophe prefix."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def slug_id(raw: Any, width: int = 5) -> str:
    """Normalize numeric catalogue ids to zero-padded digit strings."""
    if raw is None:
        raise ValueError("Missing id")
    s = normalize_text(raw)
    s = re.sub(r"\.0$", "", s)
    s = re.sub(r"\D", "", s)
    if not s:
        raise ValueError(f"Invalid id value: {raw!r}")
    return s.zfill(width)


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def coerce_int(value: Any) -> Optional[int]:
    """Integer coercion for remaining operational metadata; None if unparseable."""
    if is_empty(value):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    try:
        return int(str(value).strip())
    except Exception:
        return None


def canonicalize_for_hash(value: Any) -> Any:
    """Canonicalize values for deterministic hashing."""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda k: str(k)):
            out[str(key)] = canonicalize_for_hash(value[key])
        return out
    if isinstance(value, list):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, tuple):
        return [canonicalize_for_hash(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            return value
        if value == 0.0:
            return 0
        if value.is_integer():
            return int(value)
        return float(f"{value:.15g}")
    return value


def compute_payload_hash_hex(payload: Any) -> str:
    """Compute deterministic blake2b hex hash for a canonicalized payload."""
    canonical = json.dumps(
        canonicalize_for_hash(payload),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.blake2b(canonical, digest_size=16).hexdigest()


def compute_payload_version(payload: Any) -> str:
    """Compute deterministic blake2b content version token."""
    return f"blake2b-{compute_payload_hash_hex(payload)}"


def compact_json_value(value: Any, *, prune_empty_dicts: bool = True) -> Any:
    """Drop null object fields recursively while preserving empty lists."""
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, item in value.items():
            compacted = compact_json_value(item, prune_empty_dicts=prune_empty_dicts)
            if compacted is None:
                continue
            out[key] = compacted
        if prune_empty_dicts and not out:
            return None
        return out
    if isinstance(value, list):
        out_list = []
        for item in value:
            compacted = compact_json_value(item, prune_empty_dicts=prune_empty_dicts)
            if compacted is None:
                continue
            out_list.append(compacted)
        return out_list
    return value


def compact_json_object(payload: Dict[str, Any]) -> Dict[str, Any]:
    compacted = compact_json_value(payload, prune_empty_dicts=False)
    return compacted if isinstance(compacted, dict) else {}

"""Shared pure helpers for catalogue generation payloads."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
from typing import Any, Dict, List, Optional


def normalize_text(value: Any) -> str:
    """Normalize source text by trimming and stripping a leading apostrophe prefix."""
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def parse_date(raw: Any) -> Optional[str]:
    if raw is None or str(raw).strip() == "":
        return None
    if isinstance(raw, dt.datetime):
        return raw.date().isoformat()
    if isinstance(raw, dt.date):
        return raw.isoformat()
    s = normalize_text(raw)
    # Accept YYYY-M-D and normalise to YYYY-MM-DD if possible
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m:
        y, mo, d = map(int, m.groups())
        return dt.date(y, mo, d).isoformat()
    # Last resort: leave as-is (but upstream should be fixed)
    return s


def parse_list(raw: Any, sep: str = ",") -> List[str]:
    if raw is None:
        return []
    s = normalize_text(raw)
    if not s:
        return []
    return [item.strip() for item in s.split(sep) if item.strip()]


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def coerce_numeric(value: Any) -> Optional[float]:
    """Best-effort numeric coercion for dimension fields; returns None if not parseable."""
    if is_empty(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except Exception:
        return None


def coerce_int(value: Any) -> Optional[int]:
    """Best-effort integer coercion for year; returns None if not parseable."""
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


def coerce_string(value: Any) -> Optional[str]:
    """Coerce any non-empty value to a trimmed string."""
    if is_empty(value):
        return None
    s = normalize_text(value)
    return s if s != "" else None


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

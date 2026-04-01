from __future__ import annotations

import re
from typing import Any, List


SERIES_ID_WIDTH = 3
LEGACY_SERIES_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.startswith("'") and len(s) > 1:
        s = s[1:]
    return s


def normalize_series_id(raw: Any, *, allow_legacy_slug: bool = True, width: int = SERIES_ID_WIDTH) -> str:
    if raw is None:
        raise ValueError("Missing series_id")
    s = normalize_text(raw)
    if not s:
        raise ValueError("Missing series_id")
    s = re.sub(r"\.0+$", "", s)
    if re.fullmatch(r"\d+", s):
        return s.zfill(width)
    if allow_legacy_slug and LEGACY_SERIES_ID_RE.fullmatch(s):
        return s
    raise ValueError(f"Invalid series_id value: {raw!r}")


def parse_series_ids(raw: Any, *, allow_legacy_slug: bool = True, width: int = SERIES_ID_WIDTH) -> List[str]:
    values: List[str] = []
    seen: set[str] = set()
    for part in normalize_text(raw).split(","):
        if normalize_text(part) == "":
            continue
        sid = normalize_series_id(part, allow_legacy_slug=allow_legacy_slug, width=width)
        if sid in seen:
            continue
        seen.add(sid)
        values.append(sid)
    return values


def is_valid_series_id(raw: Any, *, allow_legacy_slug: bool = True, width: int = SERIES_ID_WIDTH) -> bool:
    try:
        normalize_series_id(raw, allow_legacy_slug=allow_legacy_slug, width=width)
    except ValueError:
        return False
    return True

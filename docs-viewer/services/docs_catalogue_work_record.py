"""Generate a Catalogue document body from one supplied generated Work record."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import sys
from typing import Any

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.semantic_tokens import serialize_catalogue_image_token  # noqa: E402


@dataclass(frozen=True)
class CatalogueWorkRecord:
    work_id: str
    title: str
    body: str


def _dimension(value: Any) -> str:
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        return ""
    return str(int(value)) if value == int(value) else str(value)


def catalogue_work_record(work: dict[str, Any]) -> CatalogueWorkRecord:
    """Return literal source content; this function performs no reads or writes."""
    work_id = work.get("work_id")
    title = work.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Generated Work title is unavailable")
    title = title.strip()
    height, width, depth = (_dimension(work.get(key)) for key in ("height_cm", "width_cm", "depth_cm"))
    dimensions = " × ".join(value for value in (height, width, depth) if value) + " cm" if height and width else ""
    summary = "\n".join(value for value in (
        str(work.get("year_display") or "").strip(),
        str(work.get("medium_caption") or "").strip(),
        dimensions,
        f"cat. {work_id}",
    ) if value)
    token = serialize_catalogue_image_token(
        target_type="work", target_id=work_id, alt=title, caption=title,
        summary=summary, placement="left", fill_width=True,
    )
    if not token:
        raise ValueError("Generated Work cannot produce a Catalogue image token")
    return CatalogueWorkRecord(work_id=work_id, title=title, body=token + "\n")

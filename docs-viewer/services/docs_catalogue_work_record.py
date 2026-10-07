"""Generate a Catalogue document body from one supplied generated Work record."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

BUILD_DIR = Path(__file__).resolve().parents[1] / "build"
if str(BUILD_DIR) not in sys.path:
    sys.path.insert(0, str(BUILD_DIR))

from docs_builder.semantic_tokens import serialize_catalogue_entry_token  # noqa: E402


@dataclass(frozen=True)
class CatalogueWorkRecord:
    work_id: str
    title: str
    body: str


def catalogue_work_record(work: dict[str, Any]) -> CatalogueWorkRecord:
    """Return the identity-only Entry and separate related-links directive."""
    work_id = work.get("work_id")
    title = work.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Generated Work title is unavailable")
    token = serialize_catalogue_entry_token(work_id)
    if not token:
        raise ValueError("Generated Work cannot produce a Catalogue Entry token")
    return CatalogueWorkRecord(work_id=work_id, title=title, body=token + "\n\n[[links|context]]\n")

"""Generate a Catalogue document body from one supplied generated Work record."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CatalogueWorkRecord:
    work_id: str
    title: str
    body: str


def catalogue_work_record(work: dict[str, Any]) -> CatalogueWorkRecord:
    """Return the identity-only Entry and separate related-links directive."""
    work_id = work["work_id"]
    return CatalogueWorkRecord(
        work_id=work_id, title=work["title"],
        body=f"[[catalogue:entry:work:{work_id}]]\n\n[[links|context]]\n",
    )

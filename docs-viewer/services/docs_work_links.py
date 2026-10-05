"""List authored canonical Work links without contacting their destinations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docs_work_resources import canonical_works

REPORT_SCHEMA = "docs_work_links_report_v1"


def work_links_report(repo_root: Path) -> dict[str, Any]:
    """Return one complete Work/label/URL row per authored link; never scan media."""
    rows = []
    for work_id, work in canonical_works(repo_root).items():
        links = work.get("links")
        if links is None:
            continue
        if not isinstance(links, list):
            raise ValueError(f"Work {work_id} links must be an array")
        title = work.get("title")
        if links and (not isinstance(title, str) or not title.strip()):
            raise ValueError(f"Work {work_id} has no title")
        for link in links:
            if not isinstance(link, dict):
                raise ValueError(f"Work {work_id} link is invalid")
            label, url = link.get("label"), link.get("url")
            if not isinstance(label, str) or not label.strip() or not isinstance(url, str) or not url.strip():
                raise ValueError(f"Work {work_id} link requires a label and URL")
            rows.append({"work": {"work_id": work_id, "title": title}, "link": {"label": label, "url": url}})
    return {"ok": True, "report": {"schema_version": REPORT_SCHEMA, "rows": rows}}

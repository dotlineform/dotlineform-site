"""List refreshed authored Work links without contacting their destinations."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_report_inputs import read_work_resources  # noqa: E402

REPORT_SCHEMA = "docs_work_links_report_v1"


def work_links_report(repo_root: Path) -> dict[str, Any]:
    """Return one complete Work/label/URL row per authored link; never scan media."""
    rows = []
    for work_id, work in read_work_resources(repo_root).items():
        for link in work["links"]:
            rows.append({"work": {"work_id": work_id, "title": work["title"]}, "link": dict(link)})
    return {"ok": True, "report": {"schema_version": REPORT_SCHEMA, "rows": rows}}

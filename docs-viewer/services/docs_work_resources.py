"""Read exact canonical Work identities for local resource reports."""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from studio.shared.python.studio_python_paths import ensure_studio_python_paths  # noqa: E402

ensure_studio_python_paths(__file__)

from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SCHEMAS, SOURCE_FILES, load_json_file  # noqa: E402

WORK_ID_PATTERN = re.compile(r"\A[0-9]{5}\Z")


def canonical_works(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Read Works once without generated data, media or workspace discovery."""
    try:
        payload = load_json_file(repo_root / DEFAULT_SOURCE_DIR / SOURCE_FILES["works"])
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError("Canonical Works data is unavailable or invalid") from error
    header = payload.get("header")
    works = payload.get("works")
    if not isinstance(header, dict) or header.get("schema") != SCHEMAS["works"] or not isinstance(works, dict):
        raise ValueError("Canonical Works data is invalid")
    for work_id, work in works.items():
        if not WORK_ID_PATTERN.fullmatch(work_id) or not isinstance(work, dict) or work.get("work_id") != work_id:
            raise ValueError("Canonical Work identity is invalid")
    return works

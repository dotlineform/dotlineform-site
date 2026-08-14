#!/usr/bin/env python3
"""Common helpers for Studio tag API handlers."""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from typing import Any


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

import script_logging  # noqa: E402


LOGS_REL_DIR = Path("var/studio/logs")
STUDIO_TAGS_API_LOG_SOURCE = Path(__file__).resolve().parents[1] / "studio_tags_api.py"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(repo_root: Path, event: str, details: dict[str, Any]) -> None:
    try:
        script_logging.append_script_log(
            STUDIO_TAGS_API_LOG_SOURCE,
            event=event,
            details=details,
            repo_root=repo_root,
            log_dir_rel=LOGS_REL_DIR,
        )
    except Exception:
        # Logging should not block local API requests.
        pass

"""Shared test import path setup for moved Studio source modules."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.studio_python_paths import ensure_studio_python_paths  # noqa: E402


ensure_studio_python_paths(__file__)

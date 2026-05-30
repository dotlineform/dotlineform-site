"""Headless Data Sharing subsystem.

This package is intentionally UI- and server-free. Local app API endpoints call
into this subsystem; browser modules and local route mounting stay outside it.
"""

from __future__ import annotations

from pathlib import Path


SUBSYSTEM_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ARTIFACT_ROOT = Path("var/analytics/data-sharing")

__all__ = ["RUNTIME_ARTIFACT_ROOT", "SUBSYSTEM_ROOT"]

"""Path contracts for Data Sharing runtime artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any


RUNTIME_ARTIFACT_ROOT = Path("var/analytics/data-sharing")


def normalize_domain(value: Any) -> str:
    domain = str(value or "").strip().lower()
    if not domain:
        raise ValueError("data_domain is required")
    if "/" in domain or "\\" in domain or domain in {".", ".."}:
        raise ValueError("data_domain must be a simple path segment")
    return domain


def domain_artifact_root(data_domain: Any) -> Path:
    return RUNTIME_ARTIFACT_ROOT / normalize_domain(data_domain)


__all__ = ["RUNTIME_ARTIFACT_ROOT", "domain_artifact_root", "normalize_domain"]

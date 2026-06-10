#!/usr/bin/env python3
"""Focused checks for Admin audit and activity ownership."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_SERVER_DIR = REPO_ROOT / "admin-app" / "app" / "server"
ADMIN_PACKAGE_DIR = ADMIN_SERVER_DIR / "admin_app"
for path in (REPO_ROOT, ADMIN_SERVER_DIR, ADMIN_PACKAGE_DIR):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from admin_audit_api import audit_get_payload, audit_post_response  # noqa: E402


def test_audit_api_routes_return_registry_and_validate_runs() -> None:
    health_payload = audit_get_payload(REPO_ROOT, "/health")
    audits_payload = audit_get_payload(REPO_ROOT, "/audits")

    assert health_payload["ok"] is True
    assert health_payload["service"] == "admin_audit_runner"
    assert "studio-ready-state" in health_payload["audits"]
    assert audits_payload["ok"] is True
    assert any(audit["audit_id"] == "studio-ready-state" for audit in audits_payload["audits"])

    with pytest.raises(ValueError, match="allowlisted"):
        audit_post_response(REPO_ROOT, "/audits/run", {"audit_id": "not-allowlisted"})

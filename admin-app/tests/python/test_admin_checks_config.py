#!/usr/bin/env python3
"""Focused tests for Admin checks config validation."""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_CHECKS_DIR = REPO_ROOT / "admin-app" / "checks"
sys.path.insert(0, str(ADMIN_CHECKS_DIR))

import admin_checks_config as checks_config  # noqa: E402


def loaded_config() -> dict[str, object]:
    return checks_config.load_checks_config(repo_root=REPO_ROOT)


def test_load_checks_config_accepts_v1_config() -> None:
    config = loaded_config()

    assert config["config_id"] == "admin-checks"
    assert set(config["scopes"]) == {"admin", "analytics", "docs-viewer", "public-site", "studio", "all"}
    assert "runtime-assets" in config["families"]
    assert config["routes"]["/library/"]["status"] == "mapped"
    assert config["routes"]["/works/"]["status"] == "inventory-only"
    assert config["routes"]["/studio/catalogue-work/"]["status"] == "inventory-only"
    assert config["reports"]["files"]["script"] == "admin-app/checks/reports/files.py"


def test_validate_checks_config_rejects_report_script_outside_reports() -> None:
    config = copy.deepcopy(loaded_config())
    config["reports"]["files"]["script"] = "admin-app/checks/audit_target_map.py"

    with pytest.raises(checks_config.ChecksConfigError, match="must be under admin-app/checks/reports/"):
        checks_config.validate_checks_config(config)


def test_validate_checks_config_rejects_unknown_route_link() -> None:
    config = copy.deepcopy(loaded_config())
    config["areas"]["search"]["routes"].append("/missing/")

    with pytest.raises(checks_config.ChecksConfigError, match="references unknown route"):
        checks_config.validate_checks_config(config)


def test_validate_run_request_rejects_unknown_scope_and_options() -> None:
    config = loaded_config()

    with pytest.raises(checks_config.ChecksConfigError, match="request.scope is unknown"):
        checks_config.validate_run_request(config, {"scope": "missing", "reports": ["files"]})

    with pytest.raises(checks_config.ChecksConfigError, match="unknown options"):
        checks_config.validate_run_request(
            config,
            {
                "scope": "docs-viewer",
                "reports": ["files"],
                "options": {"files": {"unknown": True}},
            },
        )

    with pytest.raises(checks_config.ChecksConfigError, match="files.limit must be <="):
        checks_config.validate_run_request(
            config,
            {
                "scope": "docs-viewer",
                "reports": ["files"],
                "options": {"files": {"limit": 1000}},
            },
        )

    with pytest.raises(checks_config.ChecksConfigError, match="files.sort must be one of"):
        checks_config.validate_run_request(
            config,
            {
                "scope": "docs-viewer",
                "reports": ["files"],
                "options": {"files": {"sort": "random"}},
            },
        )

    with pytest.raises(checks_config.ChecksConfigError, match="inventory-only routes"):
        checks_config.validate_run_request(
            config,
            {
                "scope": "public-site",
                "routes": ["/works/"],
                "reports": ["files"],
            },
        )

    with pytest.raises(checks_config.ChecksConfigError, match="unknown keys"):
        checks_config.validate_run_request(
            config,
            {
                "scope": "docs-viewer",
                "reports": ["files"],
                "output_root": "tmp",
            },
        )

    with pytest.raises(checks_config.ChecksConfigError, match="request.write must be a boolean"):
        checks_config.validate_run_request(
            config,
            {
                "scope": "docs-viewer",
                "reports": ["files"],
                "write": "yes",
            },
        )


def test_validate_run_request_returns_normalized_selection() -> None:
    config = loaded_config()

    payload = checks_config.validate_run_request(
        config,
        {
            "scope": "docs-viewer",
            "families": ["runtime-js"],
            "areas": ["search"],
            "routes": ["/library/"],
            "reports": ["files"],
            "options": {"files": {"limit": 10}},
            "write": True,
        },
    )

    assert payload["scope"] == "docs-viewer"
    assert payload["families"] == ["runtime-js"]
    assert payload["write"] is True

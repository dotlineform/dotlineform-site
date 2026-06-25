"""Shared fixtures for Studio app server tests."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from pathlib import Path
import sys
import tempfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from studio.app.server.studio.studio_app_config import asset_version, runtime_config, studio_shell_route_paths, validate_studio_route_registry  # noqa: E402
from studio.app.server.studio.studio_app_server import StudioAppRequestHandler, env_flag, parse_args  # noqa: E402
from studio.app.server.studio import studio_catalogue_api  # noqa: E402
from studio.app.server.studio.studio_catalogue_api import catalogue_get_payload, catalogue_post_response  # noqa: E402


def write_repo_marker(repo_root: Path) -> None:
    path = repo_root / "site-tools/config/site-tools.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"schema_version":"site_tools_config_v1"}\n', encoding="utf-8")

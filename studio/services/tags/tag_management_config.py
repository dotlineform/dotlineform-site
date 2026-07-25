"""Load the Studio-owned tag-management policy."""

from __future__ import annotations

import json
from pathlib import Path


TAG_MANAGEMENT_CONFIG_REL_PATH = Path("studio/data/config/tags/tag-management.json")
TAG_MANAGEMENT_CONFIG_VERSION = "tag_management_config_v1"


def load_tag_management_config(repo_root: Path) -> dict[str, object]:
    path = repo_root / TAG_MANAGEMENT_CONFIG_REL_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read tag-management config: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Tag-management config must be a JSON object: {path}")
    if payload.get("tag_management_config_version") != TAG_MANAGEMENT_CONFIG_VERSION:
        raise RuntimeError(f"Unsupported tag-management config version: {path}")
    groups = payload.get("groups")
    rag = payload.get("rag")
    if not isinstance(groups, dict) or not isinstance(groups.get("ordered"), list):
        raise RuntimeError(f"Tag-management config must include groups.ordered: {path}")
    if not isinstance(rag, dict) or not isinstance(rag.get("rules"), dict):
        raise RuntimeError(f"Tag-management config must include rag.rules: {path}")
    return payload


def tag_analysis_policy(repo_root: Path) -> dict[str, object]:
    payload = load_tag_management_config(repo_root)
    return {
        "groups": payload["groups"],
        "rag": payload["rag"],
    }

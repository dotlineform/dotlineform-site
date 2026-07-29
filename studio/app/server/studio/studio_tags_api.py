"""Tag API coordinator for the local Studio app server."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable


_BOOTSTRAP_START = Path(__file__).resolve()
for _candidate in (_BOOTSTRAP_START.parent, *_BOOTSTRAP_START.parents):
    if (_candidate / "site-tools" / "config" / "site-tools.json").exists():
        if str(_candidate) not in sys.path:
            sys.path.insert(0, str(_candidate))
        break

from studio.shared.python.studio_python_paths import ensure_studio_python_paths

REPO_ROOT = ensure_studio_python_paths(__file__)

from tags import tag_routes  # noqa: E402
from tags.tag_document_creation import TagDocumentCreateApplyError  # noqa: E402
from tags import tag_source_model as tag_source  # noqa: E402
from studio_tag_api.aliases import create_tag_alias_response  # noqa: E402
from studio_tag_api.aliases import delete_tag_alias_response  # noqa: E402
from studio_tag_api.aliases import mutate_tag_alias_response  # noqa: E402
from studio_tag_api.assignments import save_tags_response  # noqa: E402
from studio_tag_api.promotions import demote_tag_response  # noqa: E402
from studio_tag_api.promotions import promote_tag_alias_response  # noqa: E402
from studio_tag_api.registry import create_tag_response  # noqa: E402
from studio_tag_api.registry import mutate_tag_response  # noqa: E402


TAGS_DATA_DIR = tag_source.TAG_SOURCE_ROOT_REL_PATH
READ_ENDPOINTS = {
    "/tag-aliases": {
        "path": TAGS_DATA_DIR / "tag-aliases.json",
        "label": "Tag Aliases",
        "required_key": "aliases",
        "required_type": dict,
    },
    "/tag-assignments": {
        "path": TAGS_DATA_DIR / "tag-assignments.json",
        "label": "Tag Assignments",
        "required_key": "series",
        "required_type": dict,
    },
    "/tag-groups": {
        "path": TAGS_DATA_DIR / "tag-groups.json",
        "label": "Tag Groups",
        "required_key": "groups",
        "required_type": list,
    },
    "/tag-registry": {
        "path": TAGS_DATA_DIR / "tag-registry.json",
        "label": "Tag Registry",
        "required_key": "tags",
        "required_type": list,
    },
}
TAG_POST_PATHS = tag_routes.POST_PATHS


PostHandler = Callable[[Path, dict[str, Any], bool], dict[str, object]]

POST_HANDLERS: dict[str, PostHandler] = {
    tag_routes.SAVE_TAGS_PATH: lambda repo_root, body, dry_run: save_tags_response(repo_root, body, dry_run=dry_run),
    tag_routes.CREATE_TAG_PATH: lambda repo_root, body, dry_run: create_tag_response(
        repo_root,
        body,
        dry_run=dry_run,
    ),
    tag_routes.CREATE_ALIAS_PATH: lambda repo_root, body, dry_run: create_tag_alias_response(
        repo_root,
        body,
        dry_run=dry_run,
    ),
    tag_routes.DELETE_ALIAS_PATH: lambda repo_root, body, dry_run: delete_tag_alias_response(
        repo_root,
        body,
        dry_run=dry_run,
    ),
    tag_routes.MUTATE_ALIAS_PREVIEW_PATH: lambda repo_root, body, dry_run: mutate_tag_alias_response(
        repo_root,
        body,
        preview=True,
        dry_run=dry_run,
    ),
    tag_routes.MUTATE_ALIAS_APPLY_PATH: lambda repo_root, body, dry_run: mutate_tag_alias_response(
        repo_root,
        body,
        preview=False,
        dry_run=dry_run,
    ),
    tag_routes.PROMOTE_ALIAS_PREVIEW_PATH: lambda repo_root, body, dry_run: promote_tag_alias_response(
        repo_root,
        body,
        preview=True,
        dry_run=dry_run,
    ),
    tag_routes.PROMOTE_ALIAS_APPLY_PATH: lambda repo_root, body, dry_run: promote_tag_alias_response(
        repo_root,
        body,
        preview=False,
        dry_run=dry_run,
    ),
    tag_routes.DEMOTE_TAG_PREVIEW_PATH: lambda repo_root, body, dry_run: demote_tag_response(
        repo_root,
        body,
        preview=True,
        dry_run=dry_run,
    ),
    tag_routes.DEMOTE_TAG_APPLY_PATH: lambda repo_root, body, dry_run: demote_tag_response(
        repo_root,
        body,
        preview=False,
        dry_run=dry_run,
    ),
    tag_routes.MUTATE_TAG_PREVIEW_PATH: lambda repo_root, body, dry_run: mutate_tag_response(
        repo_root,
        body,
        preview=True,
        dry_run=dry_run,
    ),
    tag_routes.MUTATE_TAG_APPLY_PATH: lambda repo_root, body, dry_run: mutate_tag_response(
        repo_root,
        body,
        preview=False,
        dry_run=dry_run,
    ),
}


def tags_health_payload() -> dict[str, object]:
    return {
        "ok": True,
        "service": "studio_tags",
        "writes": {
            "create_tag": True,
            "create_tag_alias": True,
            "delete_tag_alias": True,
            "mutate_tag_alias": True,
            "mutate_tag_alias_preview": True,
            "mutate_tag": True,
            "mutate_tag_preview": True,
            "promote_tag_alias": True,
            "promote_tag_alias_preview": True,
            "demote_tag": True,
            "demote_tag_preview": True,
            "save_tags": True,
        },
    }


def data_payload(repo_root: Path, endpoint: str) -> dict[str, object]:
    spec = READ_ENDPOINTS.get(endpoint)
    if spec is None:
        raise FileNotFoundError("Not found")
    path = repo_root / spec["path"]
    label = str(spec["label"])
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read {label} data: {path}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} data must be a JSON object: {path}")
    required_value = payload.get(str(spec["required_key"]))
    required_type = spec["required_type"]
    if not isinstance(required_value, required_type):
        raise RuntimeError(f"{label} data must include {spec['required_key']} {required_type.__name__}: {path}")

    return {
        "ok": True,
        **payload,
    }


def tags_get_payload(repo_root: Path, path: str) -> dict[str, object]:
    if path == "/health":
        return tags_health_payload()
    return data_payload(repo_root, path)


def tags_post_response(
    repo_root: Path,
    path: str,
    body: dict[str, Any],
    *,
    dry_run: bool = False,
) -> tuple[HTTPStatus, dict[str, object]]:
    handler = POST_HANDLERS.get(path)
    if handler is None:
        raise FileNotFoundError("Not found")
    try:
        return HTTPStatus.OK, handler(repo_root, body, dry_run)
    except TagDocumentCreateApplyError as error:
        return HTTPStatus.INTERNAL_SERVER_ERROR, error.payload

#!/usr/bin/env python3
"""Plan and apply public media projection from exact publishable payloads."""

from __future__ import annotations

import html
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote

from docs_artifact_locations import (
    R2_PROVIDER,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_scope_config import DocsScopeConfig


PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION = "docs_public_media_reconciliation_v1"
IGNORED_PUBLIC_MEDIA_IDENTITIES = frozenset({".DS_Store", ".gitkeep"})
HTML_START_TAG_PATTERN = re.compile(
    r"<(?P<body>[A-Za-z][A-Za-z0-9:-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)
MEDIA_URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?<![\w:-])(?:src|href)\s*=\s*"
    r"(?:(?P<quote>[\"'])(?P<quoted_value>.*?)(?P=quote)|(?P<unquoted_value>[^\s\"'=<>`]+))",
    re.IGNORECASE,
)


def _media_identity_from_url(value: str, prefix: str) -> str:
    candidate = html.unescape(str(value or "").strip())
    normalized_prefix = prefix.rstrip("/")
    if not candidate.startswith(f"{normalized_prefix}/"):
        return ""
    identity = candidate.removeprefix(f"{normalized_prefix}/")
    identity = unquote(re.split(r"[?#]", identity, maxsplit=1)[0])
    try:
        return normalize_artifact_identity(identity)
    except ValueError:
        return ""


def referenced_public_media(
    config: DocsScopeConfig,
    payload_collections: Iterable[tuple[str, Mapping[Path, bytes]]],
) -> dict[tuple[str, str], tuple[str, ...]]:
    """Return exact media identities referenced by prospective public by-ID payloads."""

    projection = config.public_projection
    if projection is None:
        return {}
    prefixes = {
        media_type: media.served_path_prefix.rstrip("/")
        for media_type, media in projection.media.items()
    }
    references: dict[tuple[str, str], set[str]] = {}
    for collection, files in payload_collections:
        for relative_path, source_bytes in files.items():
            if len(relative_path.parts) != 2 or relative_path.parts[0] != "by-id" or relative_path.suffix != ".json":
                continue
            try:
                payload = json.loads(source_bytes.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                continue
            content_html = payload.get("content_html") if isinstance(payload, dict) else None
            if not isinstance(content_html, str):
                continue
            reference_label = f"{collection}:{relative_path.stem}" if collection else relative_path.stem
            for tag in HTML_START_TAG_PATTERN.finditer(content_html):
                for attribute in MEDIA_URL_ATTRIBUTE_PATTERN.finditer(tag.group("body")):
                    value = (
                        attribute.group("quoted_value")
                        if attribute.group("quote")
                        else attribute.group("unquoted_value")
                    )
                    for media_type, prefix in prefixes.items():
                        identity = _media_identity_from_url(value, prefix)
                        if not identity:
                            continue
                        references.setdefault((media_type, identity), set()).add(reference_label)
                        break
    return {
        key: tuple(sorted(labels))
        for key, labels in sorted(references.items())
    }


def _is_ignored_public_identity(identity: str) -> bool:
    return Path(identity).name in IGNORED_PUBLIC_MEDIA_IDENTITIES


def _type_adapters(
    repo_root: Path,
    config: DocsScopeConfig,
    media_type: str,
    *,
    remote_client: object | None,
) -> tuple[ArtifactLocationAdapter, ArtifactLocationAdapter]:
    projection = config.public_projection
    if projection is None:
        raise ValueError(f"scope {config.scope_id!r} has no public media projection")
    managed = config.media.types[media_type]
    public = projection.media[media_type]
    return (
        artifact_location_adapter(
            repo_root,
            managed.location,
            served_path_prefix=managed.served_path_prefix,
        ),
        artifact_location_adapter(
            repo_root,
            public.location,
            served_path_prefix=public.served_path_prefix,
            remote_client=remote_client,  # type: ignore[arg-type]
        ),
    )


def _remote_client(
    repo_root: Path,
    config: DocsScopeConfig,
    *,
    client: object | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> tuple[object | None, str]:
    projection = config.public_projection
    if projection is None:
        return None, "scope has no public media projection"
    locations = [media.location for media in projection.media.values()]
    try:
        return (
            authenticated_remote_client_for_locations(
                repo_root,
                locations,
                client=client,  # type: ignore[arg-type]
                env_files=env_files,
                environ=environ,
            ),
            "",
        )
    except Exception as exc:  # Media status must not block document publication.
        return None, str(exc)


def _public_stats(adapter: ArtifactLocationAdapter) -> tuple[dict[str, Any], str]:
    try:
        return (
            {
                item.identity: item
                for item in adapter.list()
                if not _is_ignored_public_identity(item.identity)
            },
            "",
        )
    except Exception as exc:
        return {}, str(exc)


def _reference_rows(
    references: Mapping[tuple[str, str], tuple[str, ...]],
    media_type: str,
) -> list[tuple[str, tuple[str, ...]]]:
    return [
        (identity, referenced_by)
        for (candidate_type, identity), referenced_by in references.items()
        if candidate_type == media_type
    ]


def plan_public_media_reconciliation(
    repo_root: Path,
    config: DocsScopeConfig,
    references: Mapping[tuple[str, str], tuple[str, ...]],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Describe copy, retention, missing, and exact stale-public actions."""

    projection = config.public_projection
    if projection is None:
        raise ValueError(f"scope {config.scope_id!r} has no public media projection")
    remote_client, remote_error = _remote_client(
        repo_root,
        config,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    types: list[dict[str, Any]] = []
    all_errors: list[str] = []
    for media_type, public in sorted(projection.media.items()):
        rows = _reference_rows(references, media_type)
        type_errors: list[str] = []
        items: list[dict[str, Any]] = []
        if public.location.provider == R2_PROVIDER and remote_error:
            type_errors.append(remote_error)
            managed_adapter = public_adapter = None
        else:
            try:
                managed_adapter, public_adapter = _type_adapters(
                    repo_root,
                    config,
                    media_type,
                    remote_client=remote_client,
                )
            except Exception as exc:
                type_errors.append(str(exc))
                managed_adapter = public_adapter = None
        public_stats: dict[str, Any] = {}
        public_list_error = ""
        if public_adapter is not None:
            public_stats, public_list_error = _public_stats(public_adapter)
            if public_list_error:
                type_errors.append(public_list_error)

        for identity, referenced_by in rows:
            managed_status = "unavailable"
            public_status = "unavailable" if public_adapter is None else "missing"
            action = "unavailable"
            size = 0
            error = ""
            managed_bytes: bytes | None = None
            if managed_adapter is not None:
                try:
                    managed_stat = managed_adapter.stat(identity)
                    if managed_stat is None:
                        managed_status = "missing"
                    else:
                        managed_bytes = managed_adapter.read(identity)
                        managed_status = "available"
                        size = len(managed_bytes)
                except Exception as exc:
                    managed_status = "unavailable"
                    error = str(exc)
                    type_errors.append(error)
            public_present = identity in public_stats
            if public_adapter is not None and not public_list_error:
                public_status = "present" if public_present else "missing"
            if managed_bytes is None:
                if public_adapter is not None and public_list_error:
                    try:
                        public_present = public_adapter.stat(identity) is not None
                        public_status = "present" if public_present else "missing"
                    except Exception as exc:
                        error = str(exc)
                        type_errors.append(error)
                action = "retain" if public_present else "missing"
            elif public_adapter is None:
                action = "unavailable"
            else:
                try:
                    public_stat = public_adapter.stat(identity)
                    public_present = public_stat is not None
                    public_status = "present" if public_present else "missing"
                    if public_present and public_adapter.read(identity) == managed_bytes:
                        action = "unchanged"
                        public_status = "current"
                    else:
                        action = "copy"
                        public_status = "different" if public_present else "missing"
                except Exception as exc:
                    action = "copy"
                    public_status = "unavailable"
                    error = str(exc)
                    type_errors.append(error)
            items.append(
                {
                    "media_type": media_type,
                    "identity": identity,
                    "provider": public.location.provider,
                    "referenced_by": list(referenced_by),
                    "managed_status": managed_status,
                    "public_status": public_status,
                    "action": action,
                    "size": size,
                    "error": error,
                }
            )

        if public_adapter is not None and not public_list_error:
            referenced_identities = {identity for identity, _referenced_by in rows}
            for identity in sorted(set(public_stats) - referenced_identities):
                items.append(
                    {
                        "media_type": media_type,
                        "identity": identity,
                        "provider": public.location.provider,
                        "referenced_by": [],
                        "managed_status": "not_checked",
                        "public_status": "stale",
                        "action": "remove",
                        "size": int(public_stats[identity].size),
                        "error": "",
                    }
                )
        unique_errors = sorted(set(error for error in type_errors if error))
        all_errors.extend(f"{media_type}: {error}" for error in unique_errors)
        types.append(
            {
                "media_type": media_type,
                "provider": public.location.provider,
                "referenced_count": len(rows),
                "available_count": sum(item["managed_status"] == "available" for item in items),
                "copy_count": sum(item["action"] == "copy" for item in items),
                "unchanged_count": sum(item["action"] == "unchanged" for item in items),
                "retained_count": sum(item["action"] == "retain" for item in items),
                "missing_count": sum(
                    item["managed_status"] in {"missing", "unavailable"}
                    for item in items
                    if item["action"] != "remove"
                ),
                "remove_count": sum(item["action"] == "remove" for item in items),
                "errors": unique_errors,
                "items": sorted(items, key=lambda item: (item["identity"], item["action"])),
            }
        )
    return {
        "schema_version": PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION,
        "operation": "status",
        "scope": config.scope_id,
        "referenced_count": len(references),
        "available_count": sum(item["available_count"] for item in types),
        "copy_count": sum(item["copy_count"] for item in types),
        "unchanged_count": sum(item["unchanged_count"] for item in types),
        "retained_count": sum(item["retained_count"] for item in types),
        "missing_count": sum(item["missing_count"] for item in types),
        "remove_count": sum(item["remove_count"] for item in types),
        "error_count": len(set(all_errors)),
        "errors": sorted(set(all_errors)),
        "types": types,
    }


def _apply_type(
    repo_root: Path,
    config: DocsScopeConfig,
    media_type: str,
    references: Mapping[tuple[str, str], tuple[str, ...]],
    *,
    remote_client: object | None,
) -> dict[str, Any]:
    projection = config.public_projection
    if projection is None:
        raise ValueError(f"scope {config.scope_id!r} has no public media projection")
    public = projection.media[media_type]
    rows = _reference_rows(references, media_type)
    results: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        managed_adapter, public_adapter = _type_adapters(
            repo_root,
            config,
            media_type,
            remote_client=remote_client,
        )
    except Exception as exc:
        error = str(exc)
        return {
            "media_type": media_type,
            "provider": public.location.provider,
            "copied_count": 0,
            "unchanged_count": 0,
            "retained_count": 0,
            "missing_count": 0,
            "removed_count": 0,
            "error_count": 1,
            "errors": [error],
            "items": [],
        }

    for identity, referenced_by in rows:
        result = {
            "media_type": media_type,
            "identity": identity,
            "provider": public.location.provider,
            "referenced_by": list(referenced_by),
            "status": "",
            "error": "",
        }
        try:
            managed_bytes = managed_adapter.read(identity)
        except FileNotFoundError:
            try:
                result["status"] = "retained" if public_adapter.stat(identity) is not None else "missing"
            except Exception as exc:
                result["status"] = "error"
                result["error"] = str(exc)
                errors.append(str(exc))
            results.append(result)
            continue
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            errors.append(str(exc))
            results.append(result)
            continue
        try:
            if public_adapter.stat(identity) is not None and public_adapter.read(identity) == managed_bytes:
                result["status"] = "unchanged"
            else:
                content_type = mimetypes.guess_type(identity)[0] or "application/octet-stream"
                public_adapter.replace(identity, managed_bytes, content_type=content_type)
                if not public_adapter.verify_bytes(identity, managed_bytes):
                    raise RuntimeError("public media bytes did not verify")
                result["status"] = "copied"
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            errors.append(str(exc))
        results.append(result)

    referenced_identities = {identity for identity, _referenced_by in rows}
    try:
        public_stats = {
            item.identity: item
            for item in public_adapter.list()
            if not _is_ignored_public_identity(item.identity)
        }
    except Exception as exc:
        errors.append(str(exc))
        public_stats = {}
    for identity in sorted(set(public_stats) - referenced_identities):
        result = {
            "media_type": media_type,
            "identity": identity,
            "provider": public.location.provider,
            "referenced_by": [],
            "status": "",
            "error": "",
        }
        try:
            public_adapter.delete(identity)
            result["status"] = "removed"
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)
            errors.append(str(exc))
        results.append(result)

    unique_errors = sorted(set(error for error in errors if error))
    return {
        "media_type": media_type,
        "provider": public.location.provider,
        "copied_count": sum(item["status"] == "copied" for item in results),
        "unchanged_count": sum(item["status"] == "unchanged" for item in results),
        "retained_count": sum(item["status"] == "retained" for item in results),
        "missing_count": sum(item["status"] == "missing" for item in results),
        "removed_count": sum(item["status"] == "removed" for item in results),
        "error_count": len(unique_errors),
        "errors": unique_errors,
        "items": sorted(results, key=lambda item: (item["identity"], item["status"])),
    }


def apply_public_media_reconciliation(
    repo_root: Path,
    config: DocsScopeConfig,
    references: Mapping[tuple[str, str], tuple[str, ...]],
    *,
    client: object | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Independently copy referenced media and remove exact stale projections."""

    projection = config.public_projection
    if projection is None:
        raise ValueError(f"scope {config.scope_id!r} has no public media projection")
    remote_client, remote_error = _remote_client(
        repo_root,
        config,
        client=client,
        env_files=env_files,
        environ=environ,
    )
    types: list[dict[str, Any]] = []
    for media_type, public in sorted(projection.media.items()):
        if public.location.provider == R2_PROVIDER and remote_error:
            types.append(
                {
                    "media_type": media_type,
                    "provider": public.location.provider,
                    "copied_count": 0,
                    "unchanged_count": 0,
                    "retained_count": 0,
                    "missing_count": 0,
                    "removed_count": 0,
                    "error_count": 1,
                    "errors": [remote_error],
                    "items": [],
                }
            )
            continue
        types.append(
            _apply_type(
                repo_root,
                config,
                media_type,
                references,
                remote_client=remote_client,
            )
        )
    errors = sorted(
        {
            f"{item['media_type']}: {error}"
            for item in types
            for error in item["errors"]
        }
    )
    return {
        "schema_version": PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION,
        "operation": "apply",
        "scope": config.scope_id,
        "referenced_count": len(references),
        "copied_count": sum(item["copied_count"] for item in types),
        "unchanged_count": sum(item["unchanged_count"] for item in types),
        "retained_count": sum(item["retained_count"] for item in types),
        "missing_count": sum(item["missing_count"] for item in types),
        "removed_count": sum(item["removed_count"] for item in types),
        "error_count": sum(item["error_count"] for item in types),
        "errors": errors,
        "types": types,
    }


def failed_public_media_reconciliation(scope: str, operation: str, error: Exception) -> dict[str, Any]:
    """Return a non-raising media result so document publication remains complete."""

    return {
        "schema_version": PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION,
        "operation": operation,
        "scope": scope,
        "referenced_count": 0,
        "available_count": 0,
        "copy_count": 0,
        "copied_count": 0,
        "unchanged_count": 0,
        "retained_count": 0,
        "missing_count": 0,
        "remove_count": 0,
        "removed_count": 0,
        "error_count": 1,
        "errors": [str(error)],
        "types": [],
    }


__all__ = [
    "PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION",
    "apply_public_media_reconciliation",
    "failed_public_media_reconciliation",
    "plan_public_media_reconciliation",
    "referenced_public_media",
]

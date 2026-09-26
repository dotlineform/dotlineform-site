#!/usr/bin/env python3
"""Plan and apply public media deployment from one accepted Preview snapshot."""

from __future__ import annotations

import hashlib
import html
import json
import mimetypes
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote

from docs_artifact_locations import (
    R2_PROVIDER,
    ArtifactLocation,
    ArtifactStat,
    ArtifactLocationAdapter,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_workspace_config import (
    DocsStageConfig, DocsPublicMediaConfig, public_media_bindings,
    load_docs_workspace_config, safe_relative_path,
)


PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION = "docs_public_media_reconciliation_v2"
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
    config: DocsStageConfig,
    payload_collections: Iterable[tuple[str, Mapping[Path, bytes]]],
) -> dict[tuple[str, str], tuple[str, ...]]:
    """Return exact media identities referenced by prospective public by-ID payloads."""

    projection = config.public_projection
    if projection is None:
        return {}
    prefixes = {
        media_type: media.served_path_prefix.rstrip("/")
        for media_type, (_collection, media) in public_media_bindings(config).items()
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


def publication_media_bindings(repo_root: Path, config: DocsStageConfig) -> dict[str, tuple[ArtifactLocation, DocsPublicMediaConfig]]:
    """Pair each shared family with its unchanged configured public destination."""
    bindings = {
        key: (collection.media.types[public.media_type].asset_location, public)
        for key, (collection, public) in public_media_bindings(config).items()
    }
    workspace = load_docs_workspace_config(repo_root)
    settings = json.loads((repo_root / "site-tools/config/site-tools.json").read_bytes())["media"]
    # Catalogue families must not collide with <collection>/<media_type> bindings.
    for key, source, prefix_key in (
        ("catalogue/works/primary", workspace.assets.work_primary, "image_works"),
        ("catalogue/works/files", workspace.assets.work_files, "files_works"),
    ):
        prefix = safe_relative_path(settings[prefix_key].strip("/"), field=f"media.{prefix_key}")
        if prefix.parts[0] == "archive":
            raise ValueError("Catalogue publication cannot write the archive")
        bindings[key] = (source, DocsPublicMediaConfig(
            key, prefix, ArtifactLocation(R2_PROVIDER, prefix),
            settings["base"].rstrip("/") + "/" + prefix.as_posix(),
        ))
    destination = workspace.catalogue.public_projection.location
    bindings["catalogue/works/thumbs"] = (workspace.assets.work_thumbnails, DocsPublicMediaConfig(
        "catalogue/works/thumbs", Path("works/thumbs"),
        ArtifactLocation(destination.provider, destination.path / "works/thumbs"),
        "/" + (destination.path / "works/thumbs").relative_to("site").as_posix(),
    ))
    return bindings


def publication_asset_references(repo_root: Path, config: DocsStageConfig, identities: list[str]) -> dict[tuple[str, str], tuple[str, ...]]:
    """Resolve exactly the identities recorded by Prepare Preview."""
    assets = load_docs_workspace_config(repo_root).assets
    bindings = publication_media_bindings(repo_root, config)
    references = {}
    for identity in identities:
        source = assets.reference_path(identity)
        matches = [(key, source.relative_to(location.path).as_posix())
                   for key, (location, _public) in bindings.items()
                   if source.is_relative_to(location.path) and source != location.path]
        if len(matches) != 1:
            raise ValueError(f"Asset has no exact public destination: {identity}")
        references[matches[0]] = ("Preview",)
    return references


def _matches_public(adapter: ArtifactLocationAdapter, identity: str, data: bytes, stat: ArtifactStat | None, *, remote: bool) -> bool:
    if stat is None or stat.size != len(data):
        return False
    if remote:
        # Transient transfer comparison, never a persisted asset hash/version.
        return stat.etag.strip('"').lower() == hashlib.md5(data, usedforsecurity=False).hexdigest()
    return adapter.read(identity) == data


def _reconcile(
    repo_root: Path, config: DocsStageConfig, references: Mapping[tuple[str, str], tuple[str, ...]],
    *, write: bool, client: object | None, env_files: Iterable[Path] | None, environ: Mapping[str, str] | None,
) -> dict[str, Any]:
    """Transfer only captured references. Listings compare metadata, never select or delete assets."""
    bindings = publication_media_bindings(repo_root, config)
    selected = sorted({key for key, _identity in references})
    if set(selected) - bindings.keys():
        raise ValueError("Preview references an unconfigured public asset family")
    remote_error = ""
    try:
        remote_client = authenticated_remote_client_for_locations(
            repo_root, [bindings[key][1].location for key in selected],
            client=client, env_files=env_files, environ=environ,
        )
    except Exception as exc:
        remote_client, remote_error = None, str(exc)
    types = []
    for key in selected:
        source, public = bindings[key]
        remote = public.location.provider == R2_PROVIDER
        rows = sorted((identity, labels) for (family, identity), labels in references.items() if family == key)
        items, errors = [], []
        try:
            source_adapter = artifact_location_adapter(repo_root, source)
            if remote and remote_error:
                raise RuntimeError(remote_error)
            destination = artifact_location_adapter(
                repo_root, public.location, served_path_prefix=public.served_path_prefix, remote_client=remote_client,
            )
            # One metadata LIST per remote family avoids thousands of HEAD/body reads.
            stats = {item.identity: item for item in destination.list()} if remote else {}
            setup_error = ""
        except Exception as exc:
            source_adapter = destination = None
            stats, setup_error = {}, str(exc)
            errors.append(setup_error)
        for identity, labels in rows:
            item = {
                "media_type": key, "identity": identity, "provider": public.location.provider,
                "referenced_by": list(labels), "source_status": "unavailable", "public_status": "unavailable",
                "action": "unavailable", "status": "error", "size": 0, "error": setup_error,
            }
            try:
                if source_adapter is None or destination is None:
                    raise RuntimeError(setup_error)
                data = source_adapter.read(identity)
                if not data:
                    raise ValueError(f"Required shared asset is empty: {key}/{identity}")
                item.update(source_status="available", size=len(data))
                stat = stats.get(identity) if remote else destination.stat(identity)
                if _matches_public(destination, identity, data, stat, remote=remote):
                    item.update(action="unchanged", status="unchanged", public_status="current")
                else:
                    item.update(action="copy", status="pending", public_status="different" if stat else "missing")
                    if write:
                        destination.replace(identity, data, content_type=mimetypes.guess_type(identity)[0] or "application/octet-stream")
                        if not _matches_public(destination, identity, data, destination.stat(identity), remote=remote):
                            raise RuntimeError(f"Published asset did not verify: {key}/{identity}")
                        item.update(status="copied", public_status="current")
            except FileNotFoundError:
                item.update(action="missing", status="error", source_status="missing",
                            error=f"Required shared asset is missing: {key}/{identity}")
                errors.append(item["error"])
            except Exception as exc:
                item.update(status="error", error=str(exc))
                errors.append(str(exc))
            items.append(item)
        errors = sorted(set(errors))
        types.append({
            "media_type": key, "provider": public.location.provider, "referenced_count": len(rows),
            "available_count": sum(item["source_status"] == "available" for item in items),
            "copy_count": sum(item["action"] == "copy" for item in items),
            "copied_count": sum(item["status"] == "copied" for item in items),
            "unchanged_count": sum(item["action"] == "unchanged" for item in items),
            "missing_count": sum(item["source_status"] in {"missing", "unavailable"} for item in items),
            "retained_count": 0, "remove_count": 0, "removed_count": 0,
            "error_count": len(errors), "errors": errors, "items": items,
        })
    errors = sorted({f"{item['media_type']}: {error}" for item in types for error in item["errors"]})
    counts = ("available_count", "copy_count", "copied_count", "unchanged_count", "missing_count",
              "retained_count", "remove_count", "removed_count")
    return {
        "schema_version": PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION,
        "operation": "apply" if write else "status", "stage": "preview", "referenced_count": len(references),
        **{key: sum(item[key] for item in types) for key in counts},
        "error_count": len(errors), "errors": errors, "types": types,
    }


def plan_public_media_reconciliation(
    repo_root: Path, config: DocsStageConfig, references: Mapping[tuple[str, str], tuple[str, ...]],
    *, client: object | None = None, env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Describe referenced current transfers and missing files without writes."""
    return _reconcile(repo_root, config, references, write=False, client=client, env_files=env_files, environ=environ)


def apply_public_media_reconciliation(
    repo_root: Path, config: DocsStageConfig, references: Mapping[tuple[str, str], tuple[str, ...]],
    *, client: object | None = None, env_files: Iterable[Path] | None = None, environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Copy referenced current bytes after preflight; asset cleanup is never implicit."""
    preflight = plan_public_media_reconciliation(repo_root, config, references, client=client, env_files=env_files, environ=environ)
    if preflight["error_count"]:
        return failed_public_media_reconciliation("apply", RuntimeError("; ".join(preflight["errors"])))
    return _reconcile(repo_root, config, references, write=True, client=client, env_files=env_files, environ=environ)


def failed_public_media_reconciliation(operation: str, error: Exception) -> dict[str, Any]:
    """Keep partial distribution failures in the owning completion/error flow."""
    return {
        "schema_version": PUBLIC_MEDIA_RECONCILIATION_SCHEMA_VERSION, "operation": operation, "stage": "preview",
        "referenced_count": 0, "available_count": 0, "copy_count": 0, "copied_count": 0, "unchanged_count": 0,
        "retained_count": 0, "missing_count": 0, "remove_count": 0, "removed_count": 0,
        "error_count": 1, "errors": [str(error)], "types": [],
    }

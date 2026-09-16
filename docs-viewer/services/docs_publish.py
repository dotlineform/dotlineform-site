#!/usr/bin/env python3
"""Preview and apply one consumer-neutral Docs Viewer workspace snapshot."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote

from docs_build_manifest import (
    BUILD_MANIFEST_FILENAME,
    BUILD_MANIFEST_SCHEMA_VERSION,
)
from docs_publication_payloads import project_published_view
from docs_public_mermaid_payload import public_mermaid_payload_requires_projection
from docs_workspace_config import (
    DocsStageConfig,
    DocsWorkspaceConfig,
    load_docs_workspace_config,
    load_docs_stage,
    resolve_location_path,
)


PUBLISH_MANIFEST_FILENAME = "publish-manifest.json"
PUBLISH_MANIFEST_SCHEMA_VERSION = "docs_publish_manifest_v2"
PUBLISH_PREVIEW_SCHEMA_VERSION = "docs_publish_preview_v1"
IGNORED_FILENAMES = frozenset({".DS_Store", ".gitkeep"})
STANDARD_DIRECTORIES = (
    Path("documents"),
    Path("search"),
    Path("references"),
    Path("reports"),
    Path("media"),
    Path("collections"),
)
HTML_START_TAG_PATTERN = re.compile(
    r"<(?P<body>[A-Za-z][A-Za-z0-9:-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)
MEDIA_URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?P<prefix>(?<![\w:-])(?:src|href|data-docs-viewer-diagram-(?:light|dark)-src)\s*=\s*)"
    r"(?:(?P<quote>[\"'])(?P<quoted_value>.*?)(?P=quote)|(?P<unquoted_value>[^\s\"'=<>`]+))",
    re.IGNORECASE,
)


def utc_now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: str, data: bytes) -> dict[str, Any]:
    return {"path": path, "size": len(data), "sha256": sha256_bytes(data)}


def files_revision(files: Mapping[Path, bytes]) -> str:
    digest = hashlib.sha256()
    for relative_path, data in sorted(files.items(), key=lambda item: item[0].as_posix()):
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_bytes(data)))
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


def _lifecycle_root(repo_root: Path, config: DocsStageConfig | DocsWorkspaceConfig, role: str) -> Path:
    if role in {"source", "generated"}:
        if not isinstance(config, DocsStageConfig):
            raise ValueError("Source and generated roots require an explicit stage")
        location = config.stage_root
    elif role == "published":
        location = config.workspace_root
    else:
        raise ValueError(f"Unknown Docs lifecycle role: {role}")
    owner_root = resolve_location_path(repo_root, location)
    root = owner_root / role
    if owner_root.is_symlink() or root.is_symlink():
        raise ValueError(f"Docs {role} root must not be a symlink")
    if not owner_root.is_dir() or not root.is_dir():
        raise FileNotFoundError(f"Docs {role} root is unavailable")
    return root.resolve()


def _managed_paths(root: Path, *, excluded: Iterable[str] = ()) -> list[Path]:
    excluded_set = set(excluded)
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(
                "Docs lifecycle output must not contain symlinks: "
                f"{path.relative_to(root).as_posix()}"
            )
        if not path.is_file() or path.name in IGNORED_FILENAMES:
            continue
        if path.relative_to(root).as_posix() in excluded_set:
            continue
        paths.append(path)
    return paths


def _files_from_root(root: Path, *, excluded: Iterable[str] = ()) -> dict[Path, bytes]:
    return {
        path.relative_to(root): path.read_bytes()
        for path in _managed_paths(root, excluded=excluded)
    }


def _read_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object")
    return payload


def _validate_generated_manifest(
    generated_root: Path,
    expected_stage: str,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    manifest_path = generated_root / BUILD_MANIFEST_FILENAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError("generated Build is incomplete: build-manifest.json is missing")
    manifest = _read_json_bytes(manifest_path.read_bytes(), "generated build manifest")
    if manifest.get("schema_version") != BUILD_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError("generated build manifest has an unsupported schema")
    if "scope" in manifest:
        raise RuntimeError("generated build manifest has retired scope identity; rebuild the stage")
    if str(manifest.get("stage") or "") != expected_stage:
        raise RuntimeError("generated build manifest has the wrong stage identity")
    generated_files = _files_from_root(
        generated_root,
        excluded=(BUILD_MANIFEST_FILENAME,),
    )
    records = [
        file_record(relative_path.as_posix(), data)
        for relative_path, data in sorted(
            generated_files.items(), key=lambda item: item[0].as_posix()
        )
    ]
    if manifest.get("files") != records or manifest.get("file_count") != len(records):
        raise RuntimeError("generated Build is stale: files do not match build-manifest.json")
    generated_revision = files_revision(generated_files)
    if manifest.get("generated_revision") != generated_revision:
        raise RuntimeError("generated Build is stale: generated revision does not match")
    return manifest, generated_files


def _flatten_tree(rows: Any, *, parent_id: str = "") -> list[dict[str, Any]]:
    flattened: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return flattened
    for value in rows:
        if not isinstance(value, dict):
            continue
        doc_id = str(value.get("doc_id") or "").strip()
        if not doc_id:
            continue
        row = dict(value)
        row["_parent_id"] = parent_id
        flattened.append(row)
        flattened.extend(_flatten_tree(value.get("children"), parent_id=doc_id))
    return flattened


def _validate_subject_associations(
    payload: dict[str, Any],
    *,
    stage: str,
    collection: str,
) -> None:
    if payload.get("schema_version") != "docs_subject_associations_v2":
        raise RuntimeError(
            f"generated subject associations for {stage}/{collection} have an unsupported schema"
        )
    if "scope" in payload or payload.get("stage") != stage or payload.get("collection") != collection:
        raise RuntimeError(
            f"generated subject associations for {stage}/{collection} have the wrong collection identity"
        )
    raw_associations = payload.get("associations")
    if not isinstance(raw_associations, list):
        raise RuntimeError(
            f"generated subject associations for {stage}/{collection} are missing associations"
        )

    seen_doc_ids: set[str] = set()
    for raw_association in raw_associations:
        if not isinstance(raw_association, dict):
            raise RuntimeError(
                f"generated subject associations for {stage}/{collection} contain an invalid association"
            )
        raw_documents = raw_association.get("documents")
        if not isinstance(raw_documents, list):
            raise RuntimeError(
                f"generated subject associations for {stage}/{collection} contain invalid documents"
            )
        for raw_document in raw_documents:
            if not isinstance(raw_document, dict):
                raise RuntimeError(
                    f"generated subject associations for {stage}/{collection} contain an invalid document"
                )
            target = raw_document.get("target")
            if not isinstance(target, dict):
                raise RuntimeError(
                    f"generated subject associations for {stage}/{collection} contain a document without a target"
                )
            doc_id = str(target.get("doc_id") or "").strip()
            if (
                "scope" in target
                or target.get("stage") != stage
                or target.get("collection") != collection
                or not doc_id
            ):
                raise RuntimeError(
                    f"generated subject associations for {stage}/{collection} contain the wrong target identity"
                )
            if doc_id in seen_doc_ids:
                raise RuntimeError(
                    f"generated subject associations for {stage}/{collection} duplicate {doc_id}"
                )
            seen_doc_ids.add(doc_id)


def _validate_prepared_index(path: Path, data: bytes, stage: str) -> None:
    """Retain index shape and identity checks without altering the prepared set."""
    parts = path.parts
    child_index = len(parts) == 4 and parts[0] == "collections" and parts[2] == "documents"
    if child_index and path.name == "subject-associations.json":
        _validate_subject_associations(
            _read_json_bytes(data, "generated subject associations"),
            stage=stage, collection=parts[1],
        )
    elif path == Path("search/index.json") or (
        len(parts) == 4 and parts[0] == "collections" and parts[2:] == ("search", "index.json")
    ):
        payload = _read_json_bytes(data, "generated Search payload")
        if not isinstance(payload.get("docs"), list) or not isinstance(payload.get("terms"), dict):
            raise RuntimeError("generated Search payload has an unsupported shape")
        if not isinstance(payload.get("header"), dict) or not isinstance(payload.get("fields"), list):
            raise RuntimeError("generated Search payload is missing header or fields")
        if payload["header"].get("schema") != "docs_viewer_search_index_v3" or payload["header"].get("stage") != stage or "scope" in payload["header"]:
            raise RuntimeError("generated Search payload has the wrong schema or stage identity")
        for postings in payload["terms"].values():
            if not isinstance(postings, dict):
                raise RuntimeError("generated Search term postings must be objects")
            if any(not isinstance(indexes, list) for indexes in postings.values()):
                raise RuntimeError("generated Search postings must be arrays")
    else:
        key = ""
        if path == Path("documents/recent.json") or (child_index and path.name == "manifest.json"):
            key = "docs"
        elif path == Path("documents/backlinks.json"):
            key = "by_target"
        elif path == Path("documents/semantic-tokens/index.json"):
            key = "occurrences"
        if key:
            payload = _read_json_bytes(data, f"generated {path}")
            if not isinstance(payload.get(key), dict if key == "by_target" else list):
                raise RuntimeError(f"generated {path} is missing {key}")


def _media_identity_from_url(value: str, prefix: str) -> str:
    candidate = html.unescape(str(value or "").strip())
    normalized_prefix = prefix.rstrip("/")
    if not candidate.startswith(f"{normalized_prefix}/"):
        return ""
    identity = unquote(re.split(r"[?#]", candidate.removeprefix(f"{normalized_prefix}/"), 1)[0])
    path = Path(identity)
    if (
        not identity
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or "\\" in identity
    ):
        return ""
    return path.as_posix()


def _published_media_bindings(config: DocsStageConfig) -> dict[str, tuple[str, str, Path]]:
    """Map every collection's generated URL to its accepted URL and snapshot path."""
    bindings = {}
    for collection in (config, *config.collections):
        child = getattr(collection, "collection", "")
        suffix = f"/collections/{child}" if child else ""
        for media_type, media in collection.media.types.items():
            key = f"{child}/{media_type}" if child else media_type
            relative = media.published_location.path.relative_to(config.workspace_root.path / "published")
            bindings[key] = (
                media.served_path_prefix.rstrip("/"),
                f"/docs/published/media{suffix}/{media_type}",
                relative,
            )
    return bindings


def _project_published_media_urls(
    config: DocsStageConfig,
    data: bytes,
) -> bytes:
    payload = _read_json_bytes(data, "generated document payload")
    content_html = payload.get("content_html")
    if not isinstance(content_html, str):
        return data
    bindings = _published_media_bindings(config)

    def replace_tag(tag: re.Match[str]) -> str:
        def replace_attribute(attribute: re.Match[str]) -> str:
            quote = attribute.group("quote") or ""
            value = (
                attribute.group("quoted_value")
                if quote
                else attribute.group("unquoted_value")
            )
            projected = value
            for prefix, published_prefix, _relative in bindings.values():
                identity = _media_identity_from_url(value, prefix)
                if identity:
                    raw_identity = value[len(prefix) + 1:]
                    suffix_match = re.search(r"[?#]", raw_identity)
                    suffix = raw_identity[suffix_match.start():] if suffix_match else ""
                    projected = f"{published_prefix}/{identity}{suffix}"
                    break
            return f"{attribute.group('prefix')}{quote}{projected}{quote}"

        return f"<{MEDIA_URL_ATTRIBUTE_PATTERN.sub(replace_attribute, tag.group('body'))}>"

    projected_html = HTML_START_TAG_PATTERN.sub(replace_tag, content_html)
    if projected_html == content_html:
        return data
    payload["content_html"] = projected_html
    return json_bytes(payload)


def _referenced_media(
    config: DocsStageConfig,
    files: Mapping[Path, bytes],
) -> dict[str, set[str]]:
    prefixes = {key: (source, published) for key, (source, published, _path) in _published_media_bindings(config).items()}
    references = {media_type: set() for media_type in prefixes}
    for relative_path, data in files.items():
        if relative_path.suffix.lower() not in {".json", ".html"}:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        if relative_path.suffix.lower() == ".json":
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            content_html = payload.get("content_html") if isinstance(payload, dict) else None
            if not isinstance(content_html, str):
                continue
            text = content_html
        for tag in HTML_START_TAG_PATTERN.finditer(text):
            for attribute in MEDIA_URL_ATTRIBUTE_PATTERN.finditer(tag.group("body")):
                value = (
                    attribute.group("quoted_value")
                    if attribute.group("quote")
                    else attribute.group("unquoted_value")
                )
                found_identity = False
                for media_type, type_prefixes in prefixes.items():
                    for prefix in type_prefixes:
                        identity = _media_identity_from_url(value, prefix)
                        if identity:
                            references[media_type].add(identity)
                            found_identity = True
                            break
                    if found_identity:
                        break
    return references


def _published_files(
    repo_root: Path,
    config: DocsStageConfig,
    generated_files: Mapping[Path, bytes],
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    index_path = Path("documents/index-tree.json")
    if index_path not in generated_files:
        raise FileNotFoundError("generated documents/index-tree.json is missing")
    index_tree = _read_json_bytes(generated_files[index_path], "generated index tree")
    # Pre-publish owns document selection. Accept every prepared collection and
    # its indexes together; Publish only projects lifecycle paths and media.
    document_ids: set[str] = set()
    files: dict[Path, bytes] = {}
    for relative_path, data in generated_files.items():
        parts = relative_path.parts
        _validate_prepared_index(relative_path, data, "pre-publish")
        if parts and (parts[0] == "media" or (
            len(parts) >= 4 and parts[0] == "collections" and parts[2] == "media"
        )):
            continue
        if parts[:2] == ("documents", ".publish") or relative_path.name == "manage-manifest.json":
            continue
        ordinary_document = len(parts) == 3 and parts[:2] == ("documents", "by-id")
        child_document = len(parts) == 5 and parts[0] == "collections" and parts[2:4] == ("documents", "by-id")
        if relative_path.suffix == ".json" and (ordinary_document or child_document):
            payload = _read_json_bytes(data, "prepared document")
            if payload.get("doc_id") != relative_path.stem:
                raise ValueError("Prepared document identity does not match its file")
            if config.public_projection is not None and public_mermaid_payload_requires_projection(payload):
                raise ValueError("Pre-publish Mermaid preparation is incomplete; rebuild Pre-publish before Publish")
            document_ids.add(relative_path.stem)
            files[relative_path] = _project_published_media_urls(config, data)
        elif relative_path == Path("documents/recent.json"):
            files[relative_path] = generated_files.get(Path("documents/.publish/recent.json"), data)
        else:
            files[relative_path] = data

    workspace = load_docs_workspace_config(repo_root)
    for path, data in list(files.items()):
        if path.suffix == ".json":
            files[path] = json_bytes(project_published_view(workspace, _read_json_bytes(data, f"prepared {path}")))
    for path, data in files.items():
        _validate_prepared_index(path, data, "published")

    tree_ids = {row["doc_id"] for row in _flatten_tree(index_tree.get("docs"))}
    ordinary_ids = {path.stem for path in files if len(path.parts) == 3 and path.parts[:2] == ("documents", "by-id") and path.suffix == ".json"}
    if tree_ids != ordinary_ids:
        raise ValueError("Prepared index tree and ordinary document set do not match")

    media_references = _referenced_media(config, files)
    bindings = _published_media_bindings(config)
    for media_type, identities in sorted(media_references.items()):
        for identity in sorted(identities):
            relative_path = bindings[media_type][2] / identity
            data = generated_files.get(relative_path)
            if data is None:
                raise FileNotFoundError(
                    "generated media required by accepted documents is missing: "
                    f"{relative_path.as_posix()}"
                )
            files[relative_path] = data

    return files, {
        "eligible_doc_ids": sorted(document_ids),
        "excluded_doc_ids": [],
        "media_references": {
            media_type: sorted(identities)
            for media_type, identities in sorted(media_references.items())
        },
    }


def _path_rows(paths: Iterable[Path]) -> list[str]:
    return [path.as_posix() for path in sorted(paths)]


def _plan_revision(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _publish_config(repo_root: Path, body: dict[str, Any]) -> DocsStageConfig:
    if "scope" in body:
        raise ValueError("scope is retired; Publish requires stage pre-publish")
    if body.get("stage") != "pre-publish":
        raise ValueError("Publish requires the Pre-publish stage")
    return load_docs_stage(repo_root, "pre-publish")


def preview_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    config = _publish_config(repo_root, body)
    generated_root = _lifecycle_root(repo_root, config, "generated")
    published_root = _lifecycle_root(repo_root, config, "published")
    build_manifest, generated_files = _validate_generated_manifest(
        generated_root,
        config.stage,
    )
    desired_files, eligibility = _published_files(repo_root, config, generated_files)
    current_files = _files_from_root(
        published_root,
        excluded=(PUBLISH_MANIFEST_FILENAME,),
    )
    desired_paths = set(desired_files)
    current_paths = set(current_files)
    added = desired_paths - current_paths
    removed = current_paths - desired_paths
    changed = {
        path
        for path in desired_paths & current_paths
        if desired_files[path] != current_files[path]
    }
    unchanged = (desired_paths & current_paths) - changed
    target_revision = files_revision(desired_files)
    current_revision = files_revision(current_files)
    plan_basis = {
        "stage": config.stage,
        "generated_revision": build_manifest["generated_revision"],
        "current_published_revision": current_revision,
        "target_published_revision": target_revision,
        "added": _path_rows(added),
        "changed": _path_rows(changed),
        "removed": _path_rows(removed),
    }
    return {
        "ok": True,
        "schema_version": PUBLISH_PREVIEW_SCHEMA_VERSION,
        "operation": "preview",
        "stage": config.stage,
        "generated_revision": build_manifest["generated_revision"],
        "current_published_revision": current_revision,
        "target_published_revision": target_revision,
        "plan_revision": _plan_revision(plan_basis),
        "added": _path_rows(added),
        "changed": _path_rows(changed),
        "removed": _path_rows(removed),
        "unchanged_count": len(unchanged),
        "added_count": len(added),
        "changed_count": len(changed),
        "removed_count": len(removed),
        "file_count": len(desired_files),
        "document_count": len(eligibility["eligible_doc_ids"]),
        "excluded_document_count": len(eligibility["excluded_doc_ids"]),
        "eligible_doc_ids": eligibility["eligible_doc_ids"],
        "excluded_doc_ids": eligibility["excluded_doc_ids"],
        "media_references": eligibility["media_references"],
        "up_to_date": not added and not changed and not removed,
        "summary_text": (
            f"Publish preview for the workspace: {len(added)} add, "
            f"{len(changed)} change, {len(removed)} remove, "
            f"{len(eligibility['eligible_doc_ids'])} documents accepted, "
            f"{len(eligibility['excluded_doc_ids'])} excluded."
        ),
    }


def _publish_manifest_payload(
    generated_revision: str,
    files: Mapping[Path, bytes],
) -> dict[str, Any]:
    records = [
        file_record(relative_path.as_posix(), data)
        for relative_path, data in sorted(files.items(), key=lambda item: item[0].as_posix())
    ]
    return {
        "schema_version": PUBLISH_MANIFEST_SCHEMA_VERSION,
        "stage": "published",
        "completed_at": utc_now(),
        "generated_revision": generated_revision,
        "published_revision": files_revision(files),
        "file_count": len(records),
        "files": records,
    }


def validate_published_snapshot(
    repo_root: Path,
) -> tuple[dict[str, Any], Path, dict[Path, bytes]]:
    """Reject missing, incomplete, or externally changed published state."""

    config = load_docs_workspace_config(repo_root)
    published_root = _lifecycle_root(repo_root, config, "published")
    manifest_path = published_root / PUBLISH_MANIFEST_FILENAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError(
            f"published snapshot for the workspace is unavailable: "
            f"{PUBLISH_MANIFEST_FILENAME} is missing"
        )
    manifest = _read_json_bytes(
        manifest_path.read_bytes(),
        "published snapshot manifest for the workspace",
    )
    if manifest.get("schema_version") != PUBLISH_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError("published snapshot for the workspace has an unsupported manifest")
    if "scope" in manifest or manifest.get("stage") != "published":
        raise RuntimeError("published snapshot must identify Published without scope; prepare and publish a fresh snapshot before activation")
    files = _files_from_root(
        published_root,
        excluded=(PUBLISH_MANIFEST_FILENAME,),
    )
    records = [
        file_record(relative_path.as_posix(), data)
        for relative_path, data in sorted(files.items(), key=lambda item: item[0].as_posix())
    ]
    if manifest.get("files") != records or manifest.get("file_count") != len(records):
        raise RuntimeError(
            f"published snapshot for the workspace is stale: files do not match "
            f"{PUBLISH_MANIFEST_FILENAME}"
        )
    revision = files_revision(files)
    if manifest.get("published_revision") != revision:
        raise RuntimeError(
            "published snapshot for the workspace is stale: revision does not match"
        )
    return manifest, published_root, files


def apply_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to publish a stage snapshot")
    preview = preview_publish(repo_root, body)
    if body.get("plan_revision") != preview["plan_revision"]:
        raise ValueError("Publish preview is stale; preview the stage again")
    if body.get("target_published_revision") != preview["target_published_revision"]:
        raise ValueError("Publish target revision does not match the confirmed preview")

    config = _publish_config(repo_root, body)
    generated_root = _lifecycle_root(repo_root, config, "generated")
    published_root = _lifecycle_root(repo_root, config, "published")
    build_manifest, generated_files = _validate_generated_manifest(
        generated_root,
        config.stage,
    )
    desired_files, _eligibility = _published_files(repo_root, config, generated_files)
    if files_revision(desired_files) != preview["target_published_revision"]:
        raise ValueError("generated output changed after Publish confirmation")

    completion_path = published_root / PUBLISH_MANIFEST_FILENAME
    if completion_path.is_symlink():
        raise ValueError("publish-manifest.json must not be a symlink")
    completion_path.unlink(missing_ok=True)

    for directory in STANDARD_DIRECTORIES:
        (published_root / directory).mkdir(parents=True, exist_ok=True)
    for _source_url, _published_url, relative in _published_media_bindings(config).values():
        (published_root / relative).mkdir(parents=True, exist_ok=True)

    for relative in preview["removed"]:
        target = published_root / Path(relative)
        if target.is_symlink():
            raise ValueError(f"published file must not be a symlink: {relative}")
        target.unlink(missing_ok=True)
    for relative in [*preview["added"], *preview["changed"]]:
        relative_path = Path(relative)
        target = published_root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise ValueError(f"published file must not be a symlink: {relative}")
        target.write_bytes(desired_files[relative_path])

    actual_files = _files_from_root(
        published_root,
        excluded=(PUBLISH_MANIFEST_FILENAME,),
    )
    if set(actual_files) != set(desired_files):
        raise RuntimeError("published snapshot file set did not verify")
    for relative_path, expected in desired_files.items():
        if actual_files[relative_path] != expected:
            raise RuntimeError(
                f"published snapshot bytes did not verify: {relative_path.as_posix()}"
            )

    manifest = _publish_manifest_payload(
        str(build_manifest["generated_revision"]),
        desired_files,
    )
    completion_path.write_bytes(json_bytes(manifest))
    if _read_json_bytes(completion_path.read_bytes(), "published completion manifest") != manifest:
        raise RuntimeError("published completion manifest did not verify")
    return {
        **preview,
        "operation": "apply",
        "applied": True,
        "publish_manifest": manifest,
        "summary_text": (
            f"Published accepted snapshot for the workspace: "
            f"{preview['added_count']} added, {preview['changed_count']} changed, "
            f"{preview['removed_count']} removed."
        ),
    }


__all__ = [
    "PUBLISH_MANIFEST_FILENAME",
    "PUBLISH_MANIFEST_SCHEMA_VERSION",
    "PUBLISH_PREVIEW_SCHEMA_VERSION",
    "apply_publish",
    "files_revision",
    "preview_publish",
    "validate_published_snapshot",
]

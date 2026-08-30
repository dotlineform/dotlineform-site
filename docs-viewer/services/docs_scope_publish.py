#!/usr/bin/env python3
"""Preview and apply one consumer-neutral Docs Viewer scope snapshot."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import unquote

from docs_scope_build_manifest import (
    BUILD_MANIFEST_FILENAME,
    BUILD_MANIFEST_SCHEMA_VERSION,
)
from docs_scope_config import (
    DocsScopeConfig,
    load_docs_scope_configs,
    resolve_location_path,
)


PUBLISH_MANIFEST_FILENAME = "publish-manifest.json"
PUBLISH_MANIFEST_SCHEMA_VERSION = "docs_scope_publish_manifest_v1"
PUBLISH_PREVIEW_SCHEMA_VERSION = "docs_scope_publish_preview_v1"
IGNORED_FILENAMES = frozenset({".DS_Store", ".gitkeep"})
STANDARD_DIRECTORIES = (
    Path("documents"),
    Path("search"),
    Path("references"),
    Path("reports"),
    Path("media"),
)
HTML_START_TAG_PATTERN = re.compile(
    r"<(?P<body>[A-Za-z][A-Za-z0-9:-]*(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)
MEDIA_URL_ATTRIBUTE_PATTERN = re.compile(
    r"(?P<prefix>(?<![\w:-])(?:src|href)\s*=\s*)"
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


def _scope_config(repo_root: Path, value: Any) -> DocsScopeConfig:
    scope = str(value or "").strip().lower()
    if not scope:
        raise ValueError("scope is required")
    config = load_docs_scope_configs(repo_root, scope_ids=(scope,)).get(scope)
    if config is None:
        raise ValueError(f"unsupported docs scope: {scope}")
    return config


def _lifecycle_root(repo_root: Path, config: DocsScopeConfig, role: str) -> Path:
    scope_root = resolve_location_path(repo_root, config.scope_root)
    root = scope_root / role
    if scope_root.is_symlink() or root.is_symlink():
        raise ValueError(f"Docs scope {config.scope_id!r} {role} root must not be a symlink")
    if not scope_root.is_dir() or not root.is_dir():
        raise FileNotFoundError(f"Docs scope {config.scope_id!r} {role} root is unavailable")
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
    expected_scope: str,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    manifest_path = generated_root / BUILD_MANIFEST_FILENAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError("generated Build is incomplete: build-manifest.json is missing")
    manifest = _read_json_bytes(manifest_path.read_bytes(), "generated build manifest")
    if manifest.get("schema_version") != BUILD_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError("generated build manifest has an unsupported schema")
    if manifest.get("scope") != expected_scope:
        raise RuntimeError("generated build manifest has the wrong scope identity")
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


def _parent_eligibility(index_tree: dict[str, Any]) -> tuple[set[str], set[str]]:
    rows = _flatten_tree(index_tree.get("docs"))
    excluded = {
        str(row.get("doc_id") or "").strip()
        for row in rows
        if row.get("publishable") is False
    }
    by_parent: dict[str, list[str]] = {}
    for row in rows:
        parent_id = str(row.get("_parent_id") or "").strip()
        doc_id = str(row.get("doc_id") or "").strip()
        if parent_id and doc_id:
            by_parent.setdefault(parent_id, []).append(doc_id)
    queue = list(excluded)
    while queue:
        parent_id = queue.pop(0)
        for child_id in by_parent.get(parent_id, []):
            if child_id in excluded:
                continue
            excluded.add(child_id)
            queue.append(child_id)
    all_ids = {str(row.get("doc_id") or "").strip() for row in rows}
    all_ids.discard("")
    return all_ids - excluded, excluded


def _published_tree_node(value: Any, excluded_ids: set[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    doc_id = str(value.get("doc_id") or "").strip()
    if not doc_id or doc_id in excluded_ids:
        return None
    row = {
        key: item
        for key, item in value.items()
        if key not in {"children", "publishable"}
    }
    children = [
        child
        for child in (
            _published_tree_node(item, excluded_ids)
            for item in value.get("children", [])
        )
        if child is not None
    ]
    if children:
        row["children"] = children
    return row


def _published_index_tree(payload: dict[str, Any], excluded_ids: set[str]) -> dict[str, Any]:
    rows = [
        row
        for row in (
            _published_tree_node(value, excluded_ids)
            for value in payload.get("docs", [])
        )
        if row is not None
    ]
    return {**payload, "docs": rows}


def _sub_scope_eligibility(
    generated_files: Mapping[Path, bytes],
) -> tuple[dict[str, set[str]], set[str]]:
    eligible_by_scope: dict[str, set[str]] = {}
    excluded: set[str] = set()
    prefix = Path("documents/sub-scopes")
    for relative_path, data in generated_files.items():
        if len(relative_path.parts) != 4 or Path(*relative_path.parts[:2]) != prefix:
            continue
        sub_scope = relative_path.parts[2]
        if relative_path.name == "manifest.json":
            payload = _read_json_bytes(data, f"generated sub-scope manifest {sub_scope}")
            rows = payload.get("docs")
            if not isinstance(rows, list):
                raise RuntimeError(f"generated sub-scope manifest {sub_scope} is missing docs")
            eligible_by_scope[sub_scope] = {
                str(row.get("doc_id") or "").strip()
                for row in rows
                if isinstance(row, dict) and str(row.get("doc_id") or "").strip()
            }
        elif relative_path.name == "manage-manifest.json":
            payload = _read_json_bytes(data, f"generated sub-scope manage manifest {sub_scope}")
            rows = payload.get("docs")
            if not isinstance(rows, list):
                raise RuntimeError(
                    f"generated sub-scope manage manifest {sub_scope} is missing docs"
                )
            excluded.update(
                str(row.get("doc_id") or "").strip()
                for row in rows
                if isinstance(row, dict) and row.get("publishable") is False
            )
    return eligible_by_scope, excluded


def _filter_recent(payload: dict[str, Any], eligible_ids: set[str]) -> dict[str, Any]:
    rows = payload.get("docs")
    if not isinstance(rows, list):
        raise RuntimeError("generated Recent payload is missing docs")
    return {
        **payload,
        "docs": [
            row
            for row in rows
            if isinstance(row, dict)
            and str(row.get("doc_id") or "").strip() in eligible_ids
        ],
    }


def _filter_search(payload: dict[str, Any], eligible_ids: set[str]) -> dict[str, Any]:
    docs = payload.get("docs")
    terms = payload.get("terms")
    header = payload.get("header")
    fields = payload.get("fields")
    if not isinstance(docs, list) or not isinstance(terms, dict):
        raise RuntimeError("generated Search payload has an unsupported shape")
    if not isinstance(header, dict) or not isinstance(fields, list):
        raise RuntimeError("generated Search payload is missing header or fields")
    retained_indexes = [
        index
        for index, row in enumerate(docs)
        if isinstance(row, dict) and str(row.get("id") or "").strip() in eligible_ids
    ]
    index_map = {old: new for new, old in enumerate(retained_indexes)}
    filtered_terms: dict[str, dict[str, list[int]]] = {}
    for term, raw_postings in terms.items():
        if not isinstance(raw_postings, dict):
            raise RuntimeError("generated Search term postings must be objects")
        postings: dict[str, list[int]] = {}
        for field, raw_indexes in raw_postings.items():
            if not isinstance(raw_indexes, list):
                raise RuntimeError("generated Search postings must be arrays")
            indexes = [index_map[index] for index in raw_indexes if index in index_map]
            if indexes:
                postings[str(field)] = indexes
        if postings:
            filtered_terms[str(term)] = postings
    filtered_docs = [docs[index] for index in retained_indexes]
    version_payload = {
        "schema": header.get("schema"),
        "scope": header.get("scope"),
        "fields": fields,
        "docs": filtered_docs,
        "terms": filtered_terms,
    }
    canonical = json.dumps(
        version_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    published_header = {
        **header,
        "version": f"blake2b-{hashlib.blake2b(canonical, digest_size=64).digest()[:16].hex()}",
        "count": len(filtered_docs),
    }
    return {
        **payload,
        "header": published_header,
        "docs": filtered_docs,
        "terms": filtered_terms,
    }


def _filter_backlinks(payload: dict[str, Any], eligible_ids: set[str]) -> dict[str, Any]:
    by_target = payload.get("by_target")
    if not isinstance(by_target, dict):
        raise RuntimeError("generated backlinks payload is missing by_target")
    filtered: dict[str, list[dict[str, Any]]] = {}
    for target_id, raw_rows in by_target.items():
        if str(target_id) not in eligible_ids or not isinstance(raw_rows, list):
            continue
        rows = [
            row
            for row in raw_rows
            if isinstance(row, dict)
            and str(row.get("doc_id") or "").strip() in eligible_ids
        ]
        if rows:
            filtered[str(target_id)] = rows
    return {**payload, "by_target": filtered}


def _filter_semantic_tokens(
    payload: dict[str, Any], eligible_ids: set[str]
) -> dict[str, Any]:
    occurrences = payload.get("occurrences")
    if not isinstance(occurrences, list):
        raise RuntimeError("generated semantic-token payload is missing occurrences")
    return {
        **payload,
        "occurrences": [
            row
            for row in occurrences
            if isinstance(row, dict)
            and str(row.get("source_doc_id") or "").strip() in eligible_ids
        ],
    }


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


def _project_published_media_urls(
    config: DocsScopeConfig,
    data: bytes,
) -> bytes:
    payload = _read_json_bytes(data, "generated document payload")
    content_html = payload.get("content_html")
    if not isinstance(content_html, str):
        return data
    prefixes = {
        media_type: media.served_path_prefix.rstrip("/")
        for media_type, media in config.media.types.items()
    }

    def replace_tag(tag: re.Match[str]) -> str:
        def replace_attribute(attribute: re.Match[str]) -> str:
            quote = attribute.group("quote") or ""
            value = (
                attribute.group("quoted_value")
                if quote
                else attribute.group("unquoted_value")
            )
            projected = value
            for media_type, prefix in prefixes.items():
                identity = _media_identity_from_url(value, prefix)
                if identity:
                    raw_identity = value[len(prefix) + 1:]
                    suffix_match = re.search(r"[?#]", raw_identity)
                    suffix = raw_identity[suffix_match.start():] if suffix_match else ""
                    projected = (
                        f"/docs/published/media/{config.scope_id}/"
                        f"{media_type}/{identity}{suffix}"
                    )
                    break
            return f"{attribute.group('prefix')}{quote}{projected}{quote}"

        return f"<{MEDIA_URL_ATTRIBUTE_PATTERN.sub(replace_attribute, tag.group('body'))}>"

    projected_html = HTML_START_TAG_PATTERN.sub(replace_tag, content_html)
    if projected_html == content_html:
        return data
    payload["content_html"] = projected_html
    return json_bytes(payload)


def _referenced_media(
    config: DocsScopeConfig,
    files: Mapping[Path, bytes],
) -> dict[str, set[str]]:
    prefixes = {
        media_type: (
            media.served_path_prefix.rstrip("/"),
            f"/docs/published/media/{config.scope_id}/{media_type}",
        )
        for media_type, media in config.media.types.items()
    }
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
    config: DocsScopeConfig,
    generated_files: Mapping[Path, bytes],
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    index_path = Path("documents/index-tree.json")
    if index_path not in generated_files:
        raise FileNotFoundError("generated documents/index-tree.json is missing")
    index_tree = _read_json_bytes(generated_files[index_path], "generated index tree")
    parent_eligible, parent_excluded = _parent_eligibility(index_tree)
    sub_scope_eligible, sub_scope_excluded = _sub_scope_eligibility(generated_files)
    eligible_ids = set(parent_eligible)
    for ids in sub_scope_eligible.values():
        eligible_ids.update(ids)
    excluded_ids = parent_excluded | sub_scope_excluded

    files: dict[Path, bytes] = {}
    for relative_path, data in generated_files.items():
        if relative_path.parts and relative_path.parts[0] == "media":
            continue
        if relative_path.parts[:2] == ("documents", ".publish"):
            continue
        if relative_path.name == "manage-manifest.json":
            continue
        if relative_path == index_path:
            files[relative_path] = json_bytes(
                _published_index_tree(index_tree, parent_excluded)
            )
            continue
        if relative_path == Path("documents/recent.json"):
            publication_recent = generated_files.get(
                Path("documents/.publish/recent.json")
            )
            recent = _read_json_bytes(
                publication_recent or data,
                "generated publication Recent payload",
            )
            files[relative_path] = json_bytes(_filter_recent(recent, eligible_ids))
            continue
        if relative_path == Path("documents/backlinks.json"):
            files[relative_path] = json_bytes(
                _filter_backlinks(
                    _read_json_bytes(data, "generated backlinks payload"),
                    eligible_ids,
                )
            )
            continue
        if relative_path == Path("documents/semantic-tokens/index.json"):
            files[relative_path] = json_bytes(
                _filter_semantic_tokens(
                    _read_json_bytes(data, "generated semantic-token payload"),
                    eligible_ids,
                )
            )
            continue
        if relative_path == Path("search/index.json"):
            files[relative_path] = json_bytes(
                _filter_search(
                    _read_json_bytes(data, "generated Search payload"),
                    eligible_ids,
                )
            )
            continue
        if (
            len(relative_path.parts) == 3
            and relative_path.parts[:2] == ("documents", "by-id")
            and relative_path.suffix == ".json"
        ):
            if relative_path.stem in parent_eligible:
                files[relative_path] = _project_published_media_urls(config, data)
            continue
        if (
            len(relative_path.parts) == 5
            and relative_path.parts[:2] == ("documents", "sub-scopes")
            and relative_path.parts[3] == "by-id"
            and relative_path.suffix == ".json"
        ):
            sub_scope = relative_path.parts[2]
            if relative_path.stem in sub_scope_eligible.get(sub_scope, set()):
                files[relative_path] = _project_published_media_urls(config, data)
            continue
        if relative_path.parts[:2] == ("references", "by-doc"):
            if relative_path.stem not in eligible_ids:
                continue
        if relative_path.parts and relative_path.parts[0] == "reports":
            if relative_path.stem in excluded_ids:
                continue
        files[relative_path] = data

    media_references = _referenced_media(config, files)
    for media_type, identities in sorted(media_references.items()):
        for identity in sorted(identities):
            relative_path = Path("media") / media_type / identity
            data = generated_files.get(relative_path)
            if data is None:
                raise FileNotFoundError(
                    "generated media required by accepted documents is missing: "
                    f"{relative_path.as_posix()}"
                )
            files[relative_path] = data

    return files, {
        "eligible_doc_ids": sorted(eligible_ids),
        "excluded_doc_ids": sorted(excluded_ids),
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


def preview_scope_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    config = _scope_config(repo_root, body.get("scope"))
    generated_root = _lifecycle_root(repo_root, config, "generated")
    published_root = _lifecycle_root(repo_root, config, "published")
    build_manifest, generated_files = _validate_generated_manifest(
        generated_root,
        config.scope_id,
    )
    desired_files, eligibility = _published_files(config, generated_files)
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
        "scope": config.scope_id,
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
        "scope": config.scope_id,
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
            f"Publish preview for {config.scope_id}: {len(added)} add, "
            f"{len(changed)} change, {len(removed)} remove, "
            f"{len(eligibility['eligible_doc_ids'])} documents accepted, "
            f"{len(eligibility['excluded_doc_ids'])} excluded."
        ),
    }


def _publish_manifest_payload(
    scope: str,
    generated_revision: str,
    files: Mapping[Path, bytes],
) -> dict[str, Any]:
    records = [
        file_record(relative_path.as_posix(), data)
        for relative_path, data in sorted(files.items(), key=lambda item: item[0].as_posix())
    ]
    return {
        "schema_version": PUBLISH_MANIFEST_SCHEMA_VERSION,
        "scope": scope,
        "completed_at": utc_now(),
        "generated_revision": generated_revision,
        "published_revision": files_revision(files),
        "file_count": len(records),
        "files": records,
    }


def validate_published_snapshot(
    repo_root: Path,
    scope: str,
) -> tuple[dict[str, Any], Path, dict[Path, bytes]]:
    """Reject missing, incomplete, or externally changed published state."""

    config = _scope_config(repo_root, scope)
    published_root = _lifecycle_root(repo_root, config, "published")
    manifest_path = published_root / PUBLISH_MANIFEST_FILENAME
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise FileNotFoundError(
            f"published snapshot for {config.scope_id} is unavailable: "
            f"{PUBLISH_MANIFEST_FILENAME} is missing"
        )
    manifest = _read_json_bytes(
        manifest_path.read_bytes(),
        f"published snapshot manifest for {config.scope_id}",
    )
    if manifest.get("schema_version") != PUBLISH_MANIFEST_SCHEMA_VERSION:
        raise RuntimeError(f"published snapshot for {config.scope_id} has an unsupported manifest")
    if manifest.get("scope") != config.scope_id:
        raise RuntimeError(f"published snapshot for {config.scope_id} has the wrong scope identity")
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
            f"published snapshot for {config.scope_id} is stale: files do not match "
            f"{PUBLISH_MANIFEST_FILENAME}"
        )
    revision = files_revision(files)
    if manifest.get("published_revision") != revision:
        raise RuntimeError(
            f"published snapshot for {config.scope_id} is stale: revision does not match"
        )
    return manifest, published_root, files


def apply_scope_publish(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    if body.get("confirm") is not True:
        raise ValueError("confirm must be true to publish a scope snapshot")
    preview = preview_scope_publish(repo_root, body)
    if body.get("plan_revision") != preview["plan_revision"]:
        raise ValueError("Publish preview is stale; preview the scope again")
    if body.get("target_published_revision") != preview["target_published_revision"]:
        raise ValueError("Publish target revision does not match the confirmed preview")

    config = _scope_config(repo_root, preview["scope"])
    generated_root = _lifecycle_root(repo_root, config, "generated")
    published_root = _lifecycle_root(repo_root, config, "published")
    build_manifest, generated_files = _validate_generated_manifest(
        generated_root,
        config.scope_id,
    )
    desired_files, _eligibility = _published_files(config, generated_files)
    if files_revision(desired_files) != preview["target_published_revision"]:
        raise ValueError("generated output changed after Publish confirmation")

    completion_path = published_root / PUBLISH_MANIFEST_FILENAME
    if completion_path.is_symlink():
        raise ValueError("publish-manifest.json must not be a symlink")
    completion_path.unlink(missing_ok=True)

    for directory in STANDARD_DIRECTORIES:
        (published_root / directory).mkdir(parents=True, exist_ok=True)
    for media_type in config.media.types:
        (published_root / "media" / media_type).mkdir(parents=True, exist_ok=True)

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
        config.scope_id,
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
            f"Published accepted snapshot for {config.scope_id}: "
            f"{preview['added_count']} added, {preview['changed_count']} changed, "
            f"{preview['removed_count']} removed."
        ),
    }


__all__ = [
    "PUBLISH_MANIFEST_FILENAME",
    "PUBLISH_MANIFEST_SCHEMA_VERSION",
    "PUBLISH_PREVIEW_SCHEMA_VERSION",
    "apply_scope_publish",
    "files_revision",
    "preview_scope_publish",
    "validate_published_snapshot",
]

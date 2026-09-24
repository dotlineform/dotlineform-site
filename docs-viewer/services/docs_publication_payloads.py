"""Stage and URL projection for accepted document payloads."""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit

from docs_document_identity import is_immutable_doc_id
from docs_workspace_config import (
    DocsWorkspaceConfig,
    public_documents_path,
    public_search_path,
    select_workspace_stage,
)


def project_public_view(config: DocsWorkspaceConfig, payload: dict[str, Any]) -> dict[str, Any]:
    """Project accepted local URLs to the configured public section and assets."""
    def asset_url(path: Path | None) -> str:
        if path is None or not path.parts or path.parts[0] != "site":
            raise ValueError("Public document destinations must remain beneath site/")
        return "/" + Path(*path.parts[1:]).as_posix()

    parent_prefix = asset_url(public_documents_path(config))
    child_prefixes = {
        child.collection: asset_url(public_documents_path(child))
        for child in select_workspace_stage(config, "preview").collections
    }

    def project_url(value: str) -> str:
        parsed = urlsplit(html.unescape(value))
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            return value
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        query = dict(pairs)
        if parsed.path in {"/docs/", config.public_viewer_base_url}:
            if "scope" in query:
                raise ValueError("Accepted document URL contains retired scope identity")
            if query.get("stage", "preview") == "preview" and is_immutable_doc_id(query.get("doc", "")):
                return parsed._replace(path=config.public_viewer_base_url, query=urlencode([(key, item) for key, item in pairs if key != "stage"])).geturl()
        external = "/docs/preview/external/"
        if parsed.path.startswith(external):
            child, separator, relative = parsed.path.removeprefix(external).partition("/")
            if not separator or child not in child_prefixes:
                raise ValueError("Accepted URL identifies an unconfigured public collection")
            return parsed._replace(path=f"{child_prefixes[child]}/{relative}").geturl()
        paths = {
            "/docs/preview/index-tree": f"{parent_prefix}/index-tree.json",
            "/docs/preview/recent": f"{parent_prefix}/recent.json",
            "/docs/preview/search": asset_url(public_search_path(config)),
        }
        if parsed.path == "/docs/preview/doc" and is_immutable_doc_id(query.get("doc_id", "")):
            return parsed._replace(path=f"{parent_prefix}/by-id/{query['doc_id']}.json", query="").geturl()
        if parsed.path in paths:
            return parsed._replace(path=paths[parsed.path], query="").geturl()
        return value

    def project(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: "published" if key in {"stage", "source_stage"} and item == "preview" else project(item) for key, item in value.items()}
        if isinstance(value, list):
            return [project(item) for item in value]
        if not isinstance(value, str):
            return value
        if value.startswith("/"):
            return project_url(value)
        if "<" not in value:
            return value

        def tag(match: re.Match[str]) -> str:
            def attribute(item: re.Match[str]) -> str:
                original = html.unescape(item[3])
                projected = project_url(original)
                return item[0] if projected == original else item[1] + item[2] + html.escape(projected, quote=True) + item[2]
            return re.sub(r"(\b(?:href|src)\s*=\s*)([\"'])(.*?)\2", attribute, match[0], flags=re.IGNORECASE | re.DOTALL)
        return re.sub(r"<[^>]+>", tag, value)

    return refresh_search_version(project(payload))


def project_preview_view(config: DocsWorkspaceConfig, payload: dict[str, Any]) -> dict[str, Any]:
    """Project prepared payload identities and URLs into the Preview snapshot."""
    def project_url(value: str) -> str:
        parsed = urlsplit(html.unescape(value))
        if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
            return value
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        query = dict(pairs)
        owns_document = parsed.path in {"/docs/", config.public_viewer_base_url}
        owns_api = parsed.path in {"/docs/doc", "/docs/index-tree", "/docs/recent", "/docs/search", "/docs/backlinks"}
        if (owns_document or owns_api) and "scope" in query:
            raise ValueError("Preview contains a retired scope target; prepare a fresh snapshot before activation")
        if query.get("stage", "preview") == "preview":
            if owns_document and is_immutable_doc_id(query.get("doc", "")):
                pairs = [(key, value) for key, value in pairs if key != "stage"]
                return parsed._replace(path="/docs/", query=urlencode([("stage", "preview"), *pairs])).geturl()
            if owns_api:
                return parsed._replace(path=parsed.path.replace("/docs/", "/docs/preview/", 1), query=urlencode([(key, value) for key, value in pairs if key != "stage"])).geturl()
        prefix = "/docs/generated/external/preview/"
        if parsed.path.startswith(prefix):
            return parsed._replace(path="/docs/preview/external/" + parsed.path.removeprefix(prefix)).geturl()
        return value

    def project(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: project(item) for key, item in value.items()}
        if isinstance(value, list):
            return [project(item) for item in value]
        if not isinstance(value, str):
            return value
        if value.startswith("/"):
            return project_url(value)
        if "<" not in value:
            return value

        def tag(match: re.Match[str]) -> str:
            def attribute(item: re.Match[str]) -> str:
                original = html.unescape(item[3])
                projected = project_url(original)
                return item[0] if projected == original else item[1] + item[2] + html.escape(projected, quote=True) + item[2]
            return re.sub(r"(\b(?:href|src)\s*=\s*)([\"'])(.*?)\2", attribute, match[0], flags=re.IGNORECASE | re.DOTALL)
        return re.sub(r"<[^>]+>", tag, value)

    return refresh_search_version(project(payload))


def refresh_search_version(payload: dict[str, Any]) -> dict[str, Any]:
    """Refresh the content receipt after projecting Search identity or URLs."""
    header = payload.get("header")
    if isinstance(header, dict) and header.get("schema") == "docs_viewer_search_index_v3":
        version_payload = {
            "schema": header["schema"], "stage": header["stage"],
            "fields": payload["fields"], "docs": payload["docs"], "terms": payload["terms"],
        }
        canonical = json.dumps(version_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        version = hashlib.blake2b(canonical, digest_size=64).digest()[:16].hex()
        payload["header"] = {**header, "version": f"blake2b-{version}"}
    return payload

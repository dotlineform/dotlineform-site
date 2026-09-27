"""Public URL projection for prepared document payloads."""

from __future__ import annotations

import html
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
    """Project accepted local URLs; Search passes through with reader-owned routes."""
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
            if "stage" in query or "scope" in query:
                raise ValueError("Accepted document URL contains retired stage or scope identity")
            if is_immutable_doc_id(query.get("doc", "")):
                return parsed._replace(path=config.public_viewer_base_url, query=urlencode(pairs)).geturl()
        external = "/docs/generated/external/"
        if parsed.path.startswith(external):
            child, separator, relative = parsed.path.removeprefix(external).partition("/")
            if not separator or child not in child_prefixes:
                raise ValueError("Accepted URL identifies an unconfigured public collection")
            return parsed._replace(path=f"{child_prefixes[child]}/{relative}").geturl()
        paths = {
            "/docs/index-tree": f"{parent_prefix}/index-tree.json",
            "/docs/recent": f"{parent_prefix}/recent.json",
            "/docs/search": asset_url(public_search_path(config)),
        }
        if parsed.path == "/docs/doc" and is_immutable_doc_id(query.get("doc_id", "")):
            return parsed._replace(path=f"{parent_prefix}/by-id/{query['doc_id']}.json", query="").geturl()
        if parsed.path in paths:
            return parsed._replace(path=paths[parsed.path], query="").geturl()
        return value

    def project(value: Any) -> Any:
        if isinstance(value, dict):
            header = value.get("header")
            if isinstance(header, dict) and header.get("schema") == "docs_viewer_search_index_v4":
                return value
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

    return project(payload)

#!/usr/bin/env python3
"""Source-model helpers for Docs Viewer source Markdown files."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    SCOPE_ROOTS,
    path_is_under_configured_sub_scope_source,
    resolve_scope_path,
)


FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SLUG_SEP_PATTERN = re.compile(r"[^a-z0-9]+")
SAFE_PLAIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&()/_'-]*$")


@dataclass
class ScopeDoc:
    scope: str
    path: Path
    source_text: str
    front_matter: Dict[str, Any]
    body: str
    doc_id: str
    title: str
    ui_status: str
    parent_id: str
    viewable: bool


def current_doc_timestamp() -> str:
    return dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")


def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", value.strip()) if part)


def slugify(value: str) -> str:
    normalized = SLUG_SEP_PATTERN.sub("-", str(value or "").strip().lower()).strip("-")
    return normalized or "new-doc"


def parse_front_matter_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == '""':
        return ""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if INTEGER_PATTERN.match(value):
        try:
            return int(value)
        except ValueError:
            return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        quote = value[0]
        inner = value[1:-1]
        if quote == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return inner
        return inner.replace("\\'", "'")
    return value


def parse_source(path: Path) -> tuple[Dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        return {}, raw

    front_matter: Dict[str, Any] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        front_matter[key.strip()] = parse_front_matter_value(raw_value)
    body = raw[match.end():]
    return front_matter, body


def format_front_matter_value(value: Any) -> str:
    if value is None:
        return '""'
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if SAFE_PLAIN_PATTERN.match(text) and text not in {"true", "false"}:
        return text
    return json.dumps(text, ensure_ascii=False)


def format_source(front_matter: Dict[str, Any], body: str) -> str:
    preferred_order = [
        "doc_id",
        "title",
        "date",
        "date_display",
        "added_date",
        "last_updated",
        "summary",
        "ui_status",
        "parent_id",
        "viewable",
    ]
    ordered_keys = [key for key in preferred_order if key in front_matter]
    ordered_keys.extend(sorted(key for key in front_matter.keys() if key not in ordered_keys))
    lines = ["---"]
    for key in ordered_keys:
        lines.append(f"{key}: {format_front_matter_value(front_matter[key])}")
    lines.append("---")
    normalized_body = body if body.startswith("\n") else "\n" + body
    return "\n".join(lines) + normalized_body


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def doc_is_viewable(front_matter: Dict[str, Any]) -> bool:
    return front_matter_boolean(front_matter, "viewable", True)


def front_matter_boolean(front_matter: Dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def normalize_ui_status(value: Any) -> str:
    return str(value or "").strip()


def default_viewable_for_scope(scope: str) -> bool:
    return scope not in {"analysis", "library"}


def normalize_scope(scope: Any) -> str:
    value = str(scope or "").strip().lower()
    if value not in SCOPE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(SCOPE_ROOTS.keys()))}")
    return value


def scope_root(repo_root: Path, scope: str) -> Path:
    return resolve_scope_path(repo_root, SCOPE_ROOTS[scope])


def scope_markdown_paths(root: Path, scope: str) -> list[Path]:
    paths = sorted(root.glob("**/*.md"))
    config = DOCS_SCOPE_CONFIGS.get(scope)
    if config:
        paths = [
            path for path in paths
            if not path_is_under_configured_sub_scope_source(path, root, config)
        ]
    nested_paths = [path for path in paths if path.parent != root]
    if nested_paths:
        nested = ", ".join(path.relative_to(root).as_posix() for path in nested_paths)
        raise ValueError(f"Nested markdown docs are not supported under {root}; move these files to the scope root: {nested}")
    return paths


def load_scope_docs(repo_root: Path, scope: str) -> list[ScopeDoc]:
    root = scope_root(repo_root, scope)
    if not root.exists():
        raise ValueError(f"missing source root for scope {scope}: {root}")

    docs: list[ScopeDoc] = []
    for path in scope_markdown_paths(root, scope):
        front_matter, body = parse_source(path)
        doc_id = str(front_matter.get("doc_id") or path.stem).strip()
        title = str(front_matter.get("title") or humanize(doc_id or path.stem)).strip() or doc_id
        ui_status = normalize_ui_status(front_matter.get("ui_status"))
        parent_id = str(front_matter.get("parent_id") or "").strip()
        viewable = doc_is_viewable(front_matter)
        docs.append(
            ScopeDoc(
                scope=scope,
                path=path,
                source_text=path.read_text(encoding="utf-8"),
                front_matter=dict(front_matter),
                body=body,
                doc_id=doc_id,
                title=title,
                ui_status=ui_status,
                parent_id=parent_id,
                viewable=viewable,
            )
        )
    validate_scope_docs(
        docs,
        allow_unknown_parent_ids=DOCS_SCOPE_CONFIGS[scope].allow_unresolved_parent_ids,
    )
    return docs


def validate_scope_docs(docs: list[ScopeDoc], *, allow_unknown_parent_ids: bool = False) -> None:
    id_seen: dict[str, ScopeDoc] = {}
    for doc in docs:
        if doc.doc_id in id_seen:
            raise ValueError(f"Duplicate doc_id {doc.doc_id!r} in scope docs")
        id_seen[doc.doc_id] = doc

    for doc in docs:
        if doc.parent_id and doc.parent_id not in id_seen:
            if allow_unknown_parent_ids:
                continue
            raise ValueError(f"Unknown parent_id {doc.parent_id!r} for doc {doc.doc_id!r}")


def scope_doc_sort_key(doc: ScopeDoc) -> tuple[Any, ...]:
    return (
        doc.title.lower(),
        doc.doc_id,
    )


def sorted_siblings(docs: list[ScopeDoc], parent_id: str) -> list[ScopeDoc]:
    return sorted((doc for doc in docs if doc.parent_id == parent_id), key=scope_doc_sort_key)


def descendant_doc_ids(docs: list[ScopeDoc], doc_id: str) -> set[str]:
    children_by_parent: dict[str, list[ScopeDoc]] = {}
    for doc in docs:
        children_by_parent.setdefault(doc.parent_id, []).append(doc)

    seen: set[str] = set()
    stack = [doc_id]
    while stack:
        current = stack.pop()
        for child in children_by_parent.get(current, []):
            if child.doc_id in seen:
                continue
            seen.add(child.doc_id)
            stack.append(child.doc_id)
    return seen


def direct_child_doc_ids(docs: list[ScopeDoc], doc_id: str) -> list[str]:
    return [doc.doc_id for doc in sorted(docs, key=scope_doc_sort_key) if doc.parent_id == doc_id]


def rewrite_doc_source(doc: ScopeDoc, front_matter_updates: Dict[str, Any]) -> str:
    timestamp = current_doc_timestamp()
    updated_front_matter = dict(doc.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
    ).strip()
    for key, value in front_matter_updates.items():
        if value is None:
            updated_front_matter.pop(key, None)
        else:
            updated_front_matter[key] = value
    updated_front_matter.pop("sort_order", None)
    return format_source(updated_front_matter, doc.body)


def rewrite_doc_placement_source(doc: ScopeDoc, parent_id: str) -> str:
    timestamp = current_doc_timestamp()
    updated_front_matter = dict(doc.front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date") or updated_front_matter.get("last_updated") or timestamp
    ).strip()
    updated_front_matter["parent_id"] = parent_id
    updated_front_matter.pop("sort_order", None)
    return format_source(updated_front_matter, doc.body)


def ensure_unique_stem(docs: list[ScopeDoc], title: str) -> str:
    base = slugify(title)
    existing_stems = {doc.path.stem for doc in docs}
    existing_ids = {doc.doc_id for doc in docs}
    candidate = base
    suffix = 2
    while candidate in existing_stems or candidate in existing_ids:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate

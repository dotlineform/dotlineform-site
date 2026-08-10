#!/usr/bin/env python3
"""Source-model helpers for Docs Viewer source Markdown files."""

from __future__ import annotations

import datetime as dt
import json
import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from docs_document_identity import (
    DOC_TIMESTAMP_FORMAT,
    IMMUTABLE_DOC_ID_PATTERN,
    allocate_doc_id,
    current_doc_timestamp,
    doc_id_matches_added_date,
    is_doc_timestamp,
    is_immutable_doc_id,
)

from docs_scope_config import (
    DOCS_SCOPE_CONFIGS,
    DOCUMENT_SOURCE_ROOTS,
    DocsScopeConfig,
    DocsSubScopeConfig,
    document_source_path,
    path_label,
    resolve_scope_path,
)
from docs_report_source import (
    ReportDescriptor,
    ReportSourceContractRequired,
    ReportSourceContract,
    build_report_source_contract,
    parse_report_source,
)
from docs_subscope_customisations import (
    sub_scope_customisation_document_groups,
    validate_sub_scope_customisation_document,
)


FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SLUG_SEP_PATTERN = re.compile(r"[^a-z0-9]+")
SAFE_PLAIN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 .,&()/_'-]*$")
RECENT_EDIT_FRONT_MATTER_FIELDS = ("title", "summary")


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
    publishable: bool
    group: str = ""
    report: ReportDescriptor | None = None


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


def parse_source_text(raw: str, *, source_name: str = "source") -> tuple[Dict[str, Any], str]:
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        if raw.startswith("---"):
            raise ValueError(f"front matter could not be parsed in {source_name}")
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


def parse_source(path: Path) -> tuple[Dict[str, Any], str]:
    return parse_source_text(path.read_text(encoding="utf-8"), source_name=path.name)


def report_source_contract_for_collection(
    repo_root: Path,
    parent_config: DocsScopeConfig,
    document_config: DocsScopeConfig | DocsSubScopeConfig,
) -> ReportSourceContract:
    """Load the one report registry with exact configured host context."""

    registry_path = repo_root / "docs-viewer/config/reports/reports.json"
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    scope_payload = json.loads(
        (repo_root / "docs-viewer/config/scopes/docs_scopes.json").read_text(
            encoding="utf-8"
        )
    )
    configured_scope_ids = (
        str(item.get("scope_id") or "").strip()
        for item in scope_payload.get("scopes", ())
        if isinstance(item, dict)
    )
    return build_report_source_contract(
        registry_payload,
        source_scope_id=parent_config.scope_id,
        configured_scope_ids=configured_scope_ids,
        configured_sub_scope_ids=(item.sub_scope for item in parent_config.sub_scopes),
        source_sub_scope_id=str(getattr(document_config, "sub_scope", "") or ""),
    )


def parse_document_report(
    source_text: str,
    front_matter: Mapping[str, Any],
    body: str,
    *,
    source_name: str,
    contract: ReportSourceContract | None,
) -> ReportDescriptor | None:
    """Parse one document report with full-source line diagnostics."""

    body_offset = len(source_text) - len(body)
    line_offset = source_text[:body_offset].count("\n")
    return parse_report_source(
        body,
        front_matter=front_matter,
        source_name=source_name,
        contract=contract,
        line_offset=line_offset,
    )


def parse_collection_document_report(
    repo_root: Path,
    parent_config: DocsScopeConfig,
    document_config: DocsScopeConfig | DocsSubScopeConfig,
    source_text: str,
    *,
    source_name: str,
) -> ReportDescriptor | None:
    """Parse one complete candidate through its exact collection contract."""

    front_matter, body = parse_source_text(source_text, source_name=source_name)
    contract = report_source_contract_for_collection(
        repo_root,
        parent_config,
        document_config,
    )
    return parse_document_report(
        source_text,
        front_matter,
        body,
        source_name=source_name,
        contract=contract,
    )


def split_source_text(
    raw: str,
    *,
    source_name: str = "source",
) -> tuple[str, Dict[str, Any], str]:
    """Return exact front-matter source, parsed metadata, and body."""

    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        raise ValueError(f"front matter could not be parsed in {source_name}")
    front_matter, body = parse_source_text(raw, source_name=source_name)
    return raw[: match.end()], front_matter, body


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
    if (
        SAFE_PLAIN_PATTERN.match(text)
        and text not in {"true", "false"}
        and not INTEGER_PATTERN.fullmatch(text)
    ):
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
        "group",
        "folder_path",
        "work_id",
        "series_id",
        "parent_id",
        "publishable",
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


def source_revision(source_bytes: bytes) -> str:
    return f"sha256:{hashlib.sha256(source_bytes).hexdigest()}"


def write_bytes_atomic(path: Path, content: bytes) -> None:
    """Atomically replace one source file with exact bytes."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(content)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def write_text_atomic_new(path: Path, text: str) -> None:
    """Atomically create one text file while refusing an existing destination."""

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        try:
            os.link(temp_path, path)
        except FileExistsError as exc:
            raise FileExistsError(f"source path already exists: {path.name}") from exc
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def advance_doc_front_matter(
    front_matter: Dict[str, Any],
    *,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Return copied front matter with one canonical document write timestamp."""

    next_timestamp = str(timestamp or current_doc_timestamp()).strip()
    if not is_doc_timestamp(next_timestamp):
        raise ValueError("document write timestamp must use YYYY-MM-DD HH:MM:SS")
    updated_front_matter = dict(front_matter)
    updated_front_matter["added_date"] = str(
        updated_front_matter.get("added_date")
        or updated_front_matter.get("last_updated")
        or next_timestamp
    ).strip()
    updated_front_matter["last_updated"] = next_timestamp
    return updated_front_matter


def recent_edit_content(front_matter: Dict[str, Any], body: str) -> tuple[str, str, str]:
    """Return only the canonical source values that make a document recently edited."""

    return (
        str(body),
        str(front_matter.get(RECENT_EDIT_FRONT_MATTER_FIELDS[0]) or "").strip(),
        str(front_matter.get(RECENT_EDIT_FRONT_MATTER_FIELDS[1]) or "").strip(),
    )


def strictly_later_doc_timestamp(
    previous_timestamp: Any,
    candidate_timestamp: Any,
) -> str:
    """Return a full candidate timestamp strictly after a comparable previous value."""

    candidate_text = str(candidate_timestamp or "").strip()
    if not is_doc_timestamp(candidate_text):
        raise ValueError("candidate document timestamp must use YYYY-MM-DD HH:MM:SS")
    previous_text = str(previous_timestamp or "").strip()
    if not is_doc_timestamp(previous_text):
        return candidate_text

    previous_value = dt.datetime.strptime(previous_text, DOC_TIMESTAMP_FORMAT)
    candidate_value = dt.datetime.strptime(candidate_text, DOC_TIMESTAMP_FORMAT)
    if candidate_value > previous_value:
        return candidate_text
    return (previous_value + dt.timedelta(seconds=1)).strftime(DOC_TIMESTAMP_FORMAT)


def advance_front_matter_for_recent_edit(
    previous_front_matter: Dict[str, Any],
    previous_body: str,
    updated_front_matter: Dict[str, Any],
    updated_body: str,
    *,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Advance last_updated only when body, title, or summary changed."""

    if recent_edit_content(previous_front_matter, previous_body) == recent_edit_content(
        updated_front_matter,
        updated_body,
    ):
        return dict(updated_front_matter)
    return advance_doc_front_matter(updated_front_matter, timestamp=timestamp)


def rewrite_front_matter_source_timestamp(
    front_matter_source: str,
    front_matter: Dict[str, Any],
    *,
    timestamp: Optional[str] = None,
) -> str:
    """Advance timestamp fields while preserving other raw front-matter lines."""

    updated_front_matter = advance_doc_front_matter(front_matter, timestamp=timestamp)
    lines = front_matter_source.splitlines(keepends=True)
    if len(lines) < 2:
        raise ValueError("source front matter could not be updated")

    field_indices: Dict[str, int] = {}
    closing_index = -1
    for index, line in enumerate(lines):
        stripped = line.strip()
        if index > 0 and stripped.startswith("---"):
            closing_index = index
        for key in ("added_date", "last_updated"):
            if re.match(rf"^[ \t]*{re.escape(key)}[ \t]*:", line):
                field_indices[key] = index
    if closing_index < 1:
        raise ValueError("source front matter closing delimiter could not be found")

    default_newline = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"
    for key in ("added_date", "last_updated"):
        rendered = (
            f"{key}: {format_front_matter_value(updated_front_matter[key])}"
            f"{default_newline}"
        )
        index = field_indices.get(key)
        if index is not None:
            newline = "\r\n" if lines[index].endswith("\r\n") else "\n"
            lines[index] = rendered.rstrip("\r\n") + newline
            continue
        if key == "added_date" and "last_updated" in field_indices:
            insert_at = field_indices["last_updated"]
        elif key == "last_updated" and "added_date" in field_indices:
            insert_at = field_indices["added_date"] + 1
        else:
            insert_at = closing_index
        lines.insert(insert_at, rendered)
        closing_index += 1
        field_indices = {
            field: (field_index + 1 if field_index >= insert_at else field_index)
            for field, field_index in field_indices.items()
        }
        field_indices[key] = insert_at

    return "".join(lines)


def doc_is_publishable(front_matter: Dict[str, Any]) -> bool:
    return front_matter_boolean(front_matter, "publishable", True)


def front_matter_boolean(front_matter: Dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def normalize_ui_status(value: Any) -> str:
    return str(value or "").strip()


def normalize_document_group(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("group must be a scalar string")
    return value.strip().lower()


def validate_sub_scope_document_metadata(
    doc: ScopeDoc,
    *,
    ui_statuses: tuple[str, ...],
    document_groups: tuple[str, ...],
    sub_scope_customisation: Any = None,
) -> None:
    """Validate metadata owned by one configured sub-scope."""

    if doc.ui_status and doc.ui_status not in ui_statuses:
        raise ValueError(
            f"Unknown ui_status {doc.ui_status!r} for sub-scope doc {doc.doc_id!r}"
        )
    if doc.group and not document_groups:
        raise ValueError(
            f"group is not configured for sub-scope doc {doc.doc_id!r}"
        )
    if doc.group and doc.group not in document_groups:
        raise ValueError(
            f"Unknown group {doc.group!r} for sub-scope doc {doc.doc_id!r}"
        )
    validate_sub_scope_customisation_document(
        sub_scope_customisation,
        doc.front_matter,
        doc_id=doc.doc_id,
    )


def collection_supports_publishable(
    config: DocsScopeConfig | DocsSubScopeConfig,
) -> bool:
    """Return whether one exact collection participates in public Publish."""

    return getattr(config, "public_projection", None) is not None


def validate_publishable_front_matter(
    front_matter: Dict[str, Any],
    *,
    collection_config: DocsScopeConfig | DocsSubScopeConfig,
    source_name: str,
) -> None:
    """Enforce the clean-cut publication field for one exact collection."""

    if "viewable" in front_matter:
        raise ValueError(
            f"legacy viewable front matter is not supported in {source_name}; "
            "use publishable only in a publish-capable collection"
        )
    if "publishable" not in front_matter:
        return
    if not collection_supports_publishable(collection_config):
        raise ValueError(
            f"publishable front matter is not supported in local collection {source_name}"
        )
    if not isinstance(front_matter["publishable"], bool):
        raise ValueError(f"publishable front matter must be a boolean in {source_name}")


def normalize_scope(scope: Any) -> str:
    value = str(scope or "").strip().lower()
    if value not in DOCUMENT_SOURCE_ROOTS:
        raise ValueError(f"scope must be one of: {', '.join(sorted(DOCUMENT_SOURCE_ROOTS.keys()))}")
    return value


def scope_root(repo_root: Path, scope: str) -> Path:
    return resolve_scope_path(repo_root, DOCUMENT_SOURCE_ROOTS[scope])


def scope_markdown_paths(root: Path) -> list[Path]:
    paths = sorted(root.glob("**/*.md"))
    nested_paths = [path for path in paths if path.parent != root]
    if nested_paths:
        nested = ", ".join(path.relative_to(root).as_posix() for path in nested_paths)
        raise ValueError(f"Nested markdown docs are not supported under {root}; move these files to the scope root: {nested}")
    return paths


def load_document_collection_docs_for_config(
    repo_root: Path,
    parent_config: DocsScopeConfig,
    document_config: DocsScopeConfig | DocsSubScopeConfig,
) -> list[ScopeDoc]:
    """Load one exact configured parent or sub-scope document collection."""

    scope = parent_config.scope_id
    root = resolve_scope_path(repo_root, document_source_path(document_config))
    sub_scope = str(getattr(document_config, "sub_scope", "") or "").strip()
    if not root.exists():
        collection = (
            f"{scope}/{sub_scope}"
            if sub_scope
            else scope
        )
        raise ValueError(f"missing source root for scope {collection}: {root}")

    report_contract: ReportSourceContract | None = None
    docs: list[ScopeDoc] = []
    for path in scope_markdown_paths(root):
        source_text = path.read_bytes().decode("utf-8")
        front_matter, body = parse_source_text(
            source_text,
            source_name=path.name,
        )
        doc_id = str(front_matter.get("doc_id") or "").strip()
        if not doc_id:
            raise ValueError(f"missing required doc_id in {path.relative_to(root).as_posix()}")
        title = str(front_matter.get("title") or humanize(doc_id or path.stem)).strip() or doc_id
        ui_status = normalize_ui_status(front_matter.get("ui_status"))
        group = normalize_document_group(front_matter.get("group"))
        parent_id = str(front_matter.get("parent_id") or "").strip()
        validate_publishable_front_matter(
            front_matter,
            collection_config=document_config,
            source_name=path.name,
        )
        publishable = doc_is_publishable(front_matter)
        try:
            report = parse_document_report(
                source_text,
                front_matter,
                body,
                source_name=path_label(repo_root, path),
                contract=report_contract,
            )
        except ReportSourceContractRequired:
            report_contract = report_source_contract_for_collection(
                repo_root,
                parent_config,
                document_config,
            )
            report = parse_document_report(
                source_text,
                front_matter,
                body,
                source_name=path_label(repo_root, path),
                contract=report_contract,
            )
        docs.append(
            ScopeDoc(
                scope=scope,
                path=path,
                source_text=source_text,
                front_matter=dict(front_matter),
                body=body,
                doc_id=doc_id,
                title=title,
                ui_status=ui_status,
                parent_id=parent_id,
                publishable=publishable,
                group=group,
                report=report,
            )
        )
    validate_scope_docs(
        docs,
        allow_unknown_parent_ids=parent_config.allow_unresolved_parent_ids,
    )
    if sub_scope:
        for doc in docs:
            validate_sub_scope_document_metadata(
                doc,
                ui_statuses=document_config.ui_statuses,
                document_groups=sub_scope_customisation_document_groups(
                    document_config.sub_scope_customisation
                ),
                sub_scope_customisation=document_config.sub_scope_customisation,
            )
    return docs


def load_scope_docs_for_config(repo_root: Path, config: DocsScopeConfig) -> list[ScopeDoc]:
    return load_document_collection_docs_for_config(repo_root, config, config)


def load_scope_docs(repo_root: Path, scope: str) -> list[ScopeDoc]:
    return load_scope_docs_for_config(repo_root, DOCS_SCOPE_CONFIGS[scope])


def load_document_collection_docs(
    repo_root: Path,
    scope: str,
    sub_scope: str = "",
) -> list[ScopeDoc]:
    """Load exactly the configured parent or named sub-scope collection."""

    parent_config = DOCS_SCOPE_CONFIGS.get(scope)
    if parent_config is None:
        raise ValueError(f"unknown Docs Viewer scope: {scope}")
    normalized_sub_scope = str(sub_scope or "").strip().lower()
    if not normalized_sub_scope:
        return load_scope_docs_for_config(repo_root, parent_config)
    matching = [
        candidate
        for candidate in parent_config.sub_scopes
        if candidate.sub_scope == normalized_sub_scope
    ]
    if len(matching) != 1:
        raise ValueError(
            f"unknown sub_scope {normalized_sub_scope!r} for scope {scope!r}"
        )
    return load_document_collection_docs_for_config(
        repo_root,
        parent_config,
        matching[0],
    )


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


def subtree_docs_in_tree_order(docs: list[ScopeDoc], root_doc_id: str) -> list[ScopeDoc]:
    docs_by_id = {doc.doc_id: doc for doc in docs}
    root = docs_by_id.get(root_doc_id)
    if root is None:
        raise FileNotFoundError(f"doc {root_doc_id!r} not found")

    children_by_parent: dict[str, list[ScopeDoc]] = {}
    for doc in docs:
        children_by_parent.setdefault(doc.parent_id, []).append(doc)
    for children in children_by_parent.values():
        children.sort(key=scope_doc_sort_key)

    ordered: list[ScopeDoc] = []
    seen: set[str] = set()

    def append_subtree(doc: ScopeDoc) -> None:
        if doc.doc_id in seen:
            return
        seen.add(doc.doc_id)
        ordered.append(doc)
        for child in children_by_parent.get(doc.doc_id, []):
            append_subtree(child)

    append_subtree(root)
    return ordered


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
    updated_front_matter = dict(doc.front_matter)
    for key, value in front_matter_updates.items():
        if value is None:
            updated_front_matter.pop(key, None)
        else:
            updated_front_matter[key] = value
    updated_front_matter.pop("sort_order", None)
    updated_front_matter = advance_front_matter_for_recent_edit(
        doc.front_matter,
        doc.body,
        updated_front_matter,
        doc.body,
    )
    return format_source(updated_front_matter, doc.body)


def rewrite_doc_placement_source(doc: ScopeDoc, parent_id: str) -> str:
    return rewrite_doc_source(doc, {"parent_id": parent_id})

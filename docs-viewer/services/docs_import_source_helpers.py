#!/usr/bin/env python3
"""Source text and summary helpers for staged Docs source imports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from docs_scope_config import DOCS_SCOPE_CONFIGS
from docs_source_model import (
    ScopeDoc,
    current_doc_timestamp,
    default_viewable_for_scope,
    format_source,
    slugify,
)

def relative_path(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def viewer_url_for(scope: str, doc_id: str) -> str:
    normalized_scope = scope if scope in DOCS_SCOPE_CONFIGS else next(iter(DOCS_SCOPE_CONFIGS))
    return f"/docs/?scope={normalized_scope}&doc={doc_id}"

def imported_body_markdown(preview: Dict[str, Any]) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    markdown = str(preview.get("markdown_preview") or "").strip()
    if markdown:
        return markdown + "\n"
    return f"# {title}\n"


def imported_source_text_for_create(preview: Dict[str, Any], docs: list[ScopeDoc], scope: str) -> str:
    title = str(preview.get("title") or "Imported Doc").strip() or "Imported Doc"
    timestamp = current_doc_timestamp()
    front_matter = {
        "doc_id": preview["proposed_doc_id"],
        "title": title,
        "added_date": timestamp,
        "last_updated": timestamp,
        "parent_id": "",
    }
    if not default_viewable_for_scope(scope):
        front_matter["viewable"] = False
    return format_source(front_matter, imported_body_markdown(preview))


def imported_source_text_for_overwrite(preview: Dict[str, Any], target: ScopeDoc) -> str:
    title = str(preview.get("title") or target.title).strip() or target.title
    timestamp = current_doc_timestamp()
    front_matter = dict(target.front_matter)
    front_matter["doc_id"] = target.doc_id
    front_matter["title"] = title
    front_matter["added_date"] = str(front_matter.get("added_date") or front_matter.get("last_updated") or timestamp).strip()
    front_matter["last_updated"] = timestamp
    front_matter["parent_id"] = target.parent_id
    front_matter.pop("sort_order", None)
    front_matter.pop("viewable", None)
    if not target.viewable:
        front_matter["viewable"] = False
    return format_source(front_matter, imported_body_markdown(preview))


def apply_replacement_title_to_preview(preview: Dict[str, Any], replacement_title: str) -> None:
    title = str(replacement_title or "").strip()
    if not title:
        raise ValueError("replacement_title is required when the proposed doc_id collides")
    preview["title"] = title
    preview["title_source"] = "replacement_title"
    preview["proposed_doc_id"] = slugify(title)
    preview["proposed_doc_id_source"] = "replacement_title"
    markdown = str(preview.get("markdown_preview") or "")
    if markdown.startswith("# "):
        lines = markdown.splitlines()
        if lines:
            lines[0] = f"# {title}"
            preview["markdown_preview"] = "\n".join(lines)


def apply_replacement_doc_id_to_preview(preview: Dict[str, Any], replacement_doc_id: str) -> None:
    raw_doc_id = str(replacement_doc_id or "").strip()
    doc_id = slugify(raw_doc_id)
    if not doc_id:
        raise ValueError("replacement_doc_id is required when the proposed filename collides")
    preview["proposed_doc_id"] = doc_id
    preview["proposed_doc_id_source"] = "replacement_doc_id"

def import_summary_text(
    operation: str,
    doc_id: str,
    staged_filename: str,
    interactive_html_written: list[Dict[str, Any]],
) -> str:
    action = "Created" if operation == "create" else "Overwrote"
    summary = f"{action} {doc_id} from {staged_filename}."
    if interactive_html_written:
        count = len(interactive_html_written)
        suffix = "" if count == 1 else "s"
        summary += f" Copied {count} interactive HTML script file{suffix}."
    return summary


def interactive_html_overwrite_summary(plans: list[Dict[str, Any]]) -> str:
    if len(plans) == 1:
        return f"Interactive HTML asset overwrite required for {plans[0]['target_path']}."
    return f"Interactive HTML asset overwrite required for {len(plans)} script files."

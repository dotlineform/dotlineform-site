"""Combine completed Working relationship records without deriving relationships."""

from pathlib import Path
from typing import Any

from docs_lifecycle_paths import load_json_object, render_json, write_text_atomic
from docs_scope_config import DocsScopeConfig, generated_documents_path, resolve_scope_path


def write_scope_links(repo_root: Path, config: DocsScopeConfig) -> dict[str, Any]:
    """Replace the Working scope aggregate after all contributing builds finish.

    Only records with both lists empty are omitted. Read every input before
    writing so an unreadable record cannot produce a successful partial result.
    Document Build owns membership, eligibility, summaries and counts.
    """
    if config.scope_id != "analysis" or config.stage != "working":
        raise ValueError("Scope Links aggregation is available only in Analysis Working")
    output = resolve_scope_path(repo_root, generated_documents_path(config))
    directory = output / "links-by-id"
    target = output / "links.json"
    if directory.is_symlink() or target.is_symlink():
        raise ValueError("Scope Links files must remain in their configured directory")
    if not directory.is_dir():
        raise FileNotFoundError("Prepared links-by-id directory is unavailable")
    documents = []
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Scope Links inputs must remain in their configured directory")
        record = load_json_object(path, f"Prepared Links record {path.name}")
        if not isinstance(record.get("incoming"), list) or not isinstance(record.get("outgoing"), list):
            raise ValueError(f"Prepared Links record {path.name} requires incoming and outgoing lists")
        if record["incoming"] or record["outgoing"]:
            documents.append(record)
    payload = {
        "schema_version": 1,
        "scope": config.scope_id,
        "stage": config.stage,
        "documents": documents,
    }
    text = render_json(payload)
    changed = not target.exists() or target.read_text(encoding="utf-8") != text
    if changed:
        write_text_atomic(target, text)
    return {"documents": len(documents), "changed": changed}

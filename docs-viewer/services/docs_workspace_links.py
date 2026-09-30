"""Combine completed Working relationship records without deriving relationships."""

from pathlib import Path
from typing import Any

from docs_json_files import load_json_object, render_json, write_text_atomic
from docs_document_identity import is_document_id
from docs_workspace_config import DocsStageConfig, generated_documents_path, resolve_workspace_path


def write_workspace_links(repo_root: Path, config: DocsStageConfig) -> dict[str, Any]:
    """Replace the Working aggregate after all contributing builds finish.

    Only records with both lists empty are omitted. Read every input before
    writing so an unreadable record cannot produce a successful partial result.
    Document Build owns membership, eligibility and unique endpoint summaries.
    """
    if config.stage != "working":
        raise ValueError("Workspace Links aggregation is available only in Working")
    output = resolve_workspace_path(repo_root, generated_documents_path(config))
    directory = output / "links-by-id"
    target = output / "links.json"
    if directory.is_symlink() or target.is_symlink():
        raise ValueError("Workspace Links files must remain in their configured directory")
    if not directory.is_dir():
        raise FileNotFoundError("Prepared links-by-id directory is unavailable")
    documents = []
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Workspace Links inputs must remain in their configured directory")
        record = load_json_object(path, f"Prepared Links record {path.name}")
        summary = record.get("self")
        if (record.get("schema_version") != 4 or not isinstance(summary, dict)
                or set(summary) != {"collection", "doc_id", "title"}
                or summary["doc_id"] != path.stem
                or not is_document_id(summary["doc_id"], collection=summary["collection"])
                or summary["collection"] not in {"", *(child.collection for child in config.collections)}):
            raise ValueError(f"Prepared Links record {path.name} has invalid document identity")
        if not isinstance(record.get("incoming"), list) or not isinstance(record.get("outgoing"), list):
            raise ValueError(f"Prepared Links record {path.name} requires incoming and outgoing lists")
        if record["incoming"] or record["outgoing"]:
            documents.append(record)
    payload = {
        "schema_version": 4,
        "documents": documents,
    }
    text = render_json(payload)
    changed = not target.exists() or target.read_text(encoding="utf-8") != text
    if changed:
        write_text_atomic(target, text)
    return {"documents": len(documents), "changed": changed}

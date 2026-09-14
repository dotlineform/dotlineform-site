"""Apply one confirmed Archive, completing Notes before removing source documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import docs_source_model as source_model
from docs_document_archive import restore_archive, working_document_url
from docs_source_config_settings import apply_scope_settings_change


class ArchiveApplyError(RuntimeError):
    """Expose the failed phase and actual document writes without automatic retries."""

    def __init__(self, error: Exception, result: dict[str, Any]):
        super().__init__(str(error))
        self.result = {**result, "ok": False, "error": str(error)}


def apply_archive(
    repo_root: Path, body: dict[str, Any], *,
    perform_write: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate the approved receipt and finish both ordinary document projections."""
    if not isinstance(body, dict) or set(body) != {"scope", "stage", "receipt", "confirm"}:
        raise ValueError("Archive apply requires scope, stage, receipt and confirm")
    if body["confirm"] is not True:
        raise ValueError("Archive must be confirmed")
    receipt = body["receipt"]
    if not isinstance(receipt, dict) or any(receipt.get(key) != body[key] for key in ("scope", "stage")):
        raise ValueError("Archive receipt does not match the request")
    plan = restore_archive(repo_root, receipt)
    if perform_write is None:
        from docs_write_rebuild import perform_source_write_and_rebuild
        perform_write = perform_source_write_and_rebuild
    ids = [item.original.doc_id for item in plan.documents]
    written: list[Path] = []
    removed: list[str] = []
    result: dict[str, Any] = {"ok": False, "phase": "notes", "written_doc_ids": [], "removed_doc_ids": removed}

    def write_notes() -> None:
        for copy in plan.media:
            if copy.source.read_bytes() != copy.content:
                raise ValueError("Archive source media changed")
            if copy.destination.is_symlink() or (copy.destination.exists() and copy.destination.read_bytes() != copy.content):
                raise ValueError("Archive destination media changed")
        for copy in plan.media:
            if not copy.destination.exists():
                copy.destination.parent.mkdir(parents=True, exist_ok=True)
                with copy.destination.open("xb") as output:
                    output.write(copy.content)
        for item in plan.documents:
            source_model.write_text_atomic_new(item.destination, item.text)
            written.append(item.destination)
            result["written_doc_ids"].append(item.original.doc_id)

    def remove_sources() -> None:
        for item in plan.documents:
            if item.original.path.read_text(encoding="utf-8") != item.original.source_text:
                raise ValueError("Archive source document changed")
        if plan.source.parent_config.default_doc_id in ids:
            apply_scope_settings_change(repo_root, plan.source.scope, {"default_doc_id": ""}, stage="working")
        for item in plan.documents:
            item.original.path.unlink()
            removed.append(item.original.doc_id)

    try:
        perform_write(
            repo_root, "notes", [item.destination for item in plan.documents], write_notes,
            stage="working", docs_doc_ids=ids, written_paths=written,
            suppression_reason="docs-archive", skip_media_builds=True,
        )
        result["phase"] = "source"
        perform_write(
            repo_root, plan.source.scope, [item.original.path for item in plan.documents], remove_sources,
            stage="working", docs_doc_ids=ids, written_paths=[],
            suppression_reason="docs-archive", skip_media_builds=True,
        )
    except Exception as error:
        raise ArchiveApplyError(error, result) from error
    return {
        "ok": True, "archived_count": len(ids),
        "viewer_url": working_document_url(plan.target.parent_config, plan.documents[0].original.doc_id),
    }

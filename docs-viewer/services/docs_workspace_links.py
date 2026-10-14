"""Refresh the Links report snapshot from current Working relationships."""

from pathlib import Path
from typing import Any

from docs_json_files import load_json_object, render_json, write_text_atomic
from docs_workspace_config import DocsStageConfig


def write_workspace_links(config: DocsStageConfig, *, report_path: Path) -> dict[str, Any]:
    """Persist and return the report from saved per-document records.

    Only records with both lists empty are omitted. Read every input before
    writing so an unreadable record cannot produce a successful partial result.
    Document Build owns membership, eligibility and unique endpoint summaries.
    Refresh trusts those completed records. The caller supplies the confined
    report target from workspace configuration; Build never writes this report.
    """
    if config.stage != "working":
        raise ValueError("Workspace Links aggregation is available only in Working")
    directory = config.generated.documents.location.path / "links-by-id"
    if directory.is_symlink():
        raise ValueError("Workspace Links inputs must remain in their configured directory")
    if not directory.is_dir():
        raise FileNotFoundError("Prepared links-by-id directory is unavailable")
    documents = []
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise ValueError("Workspace Links inputs must remain in their configured directory")
        record = load_json_object(path, f"Prepared Links record {path.name}")
        if record["incoming"] or record["outgoing"]:
            documents.append(record)
    payload = {
        "schema_version": 4,
        "documents": documents,
    }
    text = render_json(payload)
    try:
        previous = report_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        previous = None
    if previous != text:
        write_text_atomic(report_path, text)
    return payload

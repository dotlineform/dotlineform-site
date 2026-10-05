"""Saved Broken Links results; only an explicit refresh audits and writes."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from docs_broken_links import audit_docs_broken_links
from docs_document_identity import is_document_id
from docs_document_location import canonical_document_viewer_url
from docs_json_files import render_json, write_text_atomic
from docs_management_context import log_event
from docs_workspace_config import COLLECTION_ID_PATTERN, load_docs_workspace_config


SCHEMA_VERSION = "docs_broken_links_report_v1"
SCAN_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
SOURCE_FIELDS = {"from_page_text", "from_page_url", "from_page_collection", "from_page_doc_id"}


def _safe_issue_url(value: str) -> bool:
    if not value:
        return True
    if value != value.strip() or "\\" in value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        return False
    parsed = urlsplit(value)
    return bool(
        (parsed.scheme in {"http", "https"} and parsed.netloc)
        or (not parsed.scheme and not parsed.netloc and value.startswith("/") and not value.startswith("//"))
    )


def validate_broken_links_report(report: Any) -> dict[str, Any]:
    """Validate the saved result without consulting current sources or targets."""
    if not isinstance(report, dict) or set(report) != {"schema_version", "scanned_at", "summary", "entries", "unavailable_sources"}:
        raise ValueError("Broken Links report has an invalid shape")
    timestamp = report["scanned_at"]
    if report["schema_version"] != SCHEMA_VERSION or not isinstance(timestamp, str) or not SCAN_TIME.fullmatch(timestamp):
        raise ValueError("Broken Links report has an unsupported schema or scan time")
    dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    entries, unavailable = report["entries"], report["unavailable_sources"]
    if not isinstance(entries, list) or not isinstance(unavailable, list):
        raise ValueError("Broken Links report requires issue and unscanned-source lists")
    summary = report["summary"]
    if not isinstance(summary, dict) or set(summary) != {"total"} or type(summary["total"]) is not int or summary["total"] != len(entries):
        raise ValueError("Broken Links report has an invalid issue count")
    for row in (*entries, *unavailable):
        if not isinstance(row, dict) or any(not isinstance(row.get(field), str) for field in SOURCE_FIELDS):
            raise ValueError("Broken Links report has an invalid source record")
        collection = row["from_page_collection"]
        if (collection and not COLLECTION_ID_PATTERN.fullmatch(collection)) or not is_document_id(row["from_page_doc_id"], collection=collection):
            raise ValueError("Broken Links report has an invalid source identity")
        if row["from_page_url"] != canonical_document_viewer_url(row["from_page_doc_id"], collection=collection):
            raise ValueError("Broken Links report has a mismatched source URL")
    for entry in entries:
        if any(not isinstance(entry.get(field), str) for field in ("link_text", "link_url")):
            raise ValueError("Broken Links report has an invalid issue record")
        if not _safe_issue_url(entry["link_url"]):
            raise ValueError("Broken Links report has an unsafe issue URL")
        if entry.get("issue_type") == "semantic_token" and any(not isinstance(entry.get(field), str) for field in ("raw", "reason")):
            raise ValueError("Broken Links report has an invalid token issue")
    return report


def read_broken_links(repo_root: Path) -> dict[str, Any]:
    """Read only the configured snapshot; absence is an empty, unscanned report."""
    path = load_docs_workspace_config(repo_root).broken_links_report.path
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"ok": True, "report": None}
    except (OSError, UnicodeError) as error:
        raise ValueError("Saved Broken Links report is unreadable. Use Refresh to regenerate it.") from error
    try:
        report = validate_broken_links_report(json.loads(text))
    except (ValueError, TypeError) as error:
        raise ValueError("Saved Broken Links report is invalid. Use Refresh to regenerate it.") from error
    return {"ok": True, "report": report}


def handle_broken_links(repo_root: Path, body: dict[str, Any]) -> dict[str, Any]:
    """Await the complete audit and save its result before returning success."""
    if not isinstance(body, dict) or body:
        raise ValueError("Broken Links refresh requires an empty request object")
    path = load_docs_workspace_config(repo_root).broken_links_report.path
    payload = audit_docs_broken_links(repo_root)
    report = validate_broken_links_report({
        "schema_version": SCHEMA_VERSION,
        "scanned_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "summary": payload["summary"],
        "entries": payload["entries"],
        "unavailable_sources": payload["unavailable_sources"],
    })
    try:
        write_text_atomic(path, render_json(report))
    except OSError as error:
        raise ValueError("Broken Links report could not be saved. Use Refresh to retry.") from error
    log_event(
        repo_root,
        "docs_broken_links",
        {
            "total": report["summary"]["total"],
        },
    )
    return {"ok": True, "report": report}

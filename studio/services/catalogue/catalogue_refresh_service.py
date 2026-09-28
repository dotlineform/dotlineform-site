"""Reconcile Catalogue reader output and record verified local freshness."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from catalogue.catalogue_galleries import GALLERIES_FILE, MEMBERSHIPS_FILE
from catalogue.catalogue_source import DEFAULT_SOURCE_DIR, SOURCE_FILES, records_from_json_source
from catalogue.catalogue_works_metadata import generate_catalogue_works_metadata
from catalogue.generate_work_pages import generate_catalogue_json
from catalogue.works_collection_metadata import generate_works_collection_metadata


RECEIPT_PATH = Path("var/studio/catalogue/refresh-receipt.json")
RECEIPT_SCHEMA = "catalogue_refresh_receipt_v1"
REVISION_PATHS = (
    *(DEFAULT_SOURCE_DIR / name for name in (SOURCE_FILES["works"], SOURCE_FILES["series"], GALLERIES_FILE, MEMBERSHIPS_FILE)),
    Path("_data/pipeline.json"),
    Path("site-tools/config/site-tools.json"),
)


def _receipt_path(repo_root: Path) -> Path:
    root = repo_root.resolve()
    path = root / RECEIPT_PATH
    if not path.parent.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("Catalogue Refresh receipt must remain inside the repository")
    return path


def _source_revision(repo_root: Path) -> str:
    digest = hashlib.sha256()
    for relative in REVISION_PATHS:
        path = repo_root / relative
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        if relative.is_relative_to(DEFAULT_SOURCE_DIR) or path.exists():
            digest.update(b"\1" + path.read_bytes())
        else:
            digest.update(b"\0")
        digest.update(b"\0")
    return digest.hexdigest()


def catalogue_refresh_status(repo_root: Path) -> dict[str, Any]:
    """Compare the receipt with current canonical inputs; missing receipts need Refresh."""
    try:
        revision = _source_revision(repo_root)
        path = _receipt_path(repo_root)
    except (OSError, ValueError) as error:
        raise RuntimeError(f"Catalogue Refresh status is unavailable: {error}") from error
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        receipt = None
    if isinstance(receipt, dict) and receipt.get("schema") == RECEIPT_SCHEMA and receipt.get("source_revision") == revision:
        refreshed_at = receipt.get("refreshed_at_utc")
        if isinstance(refreshed_at, str) and refreshed_at:
            return {"ok": True, "needed": False, "refreshed_at_utc": refreshed_at}
    return {"ok": True, "needed": True}


def invalidate_refresh_receipt(repo_root: Path) -> None:
    """Keep failed or incomplete work from presenting an older completion as current."""
    _receipt_path(repo_root).unlink(missing_ok=True)


def _write_receipt(repo_root: Path, revision: str) -> dict[str, Any]:
    path = _receipt_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "source_revision": revision,
        "refreshed_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    data = (json.dumps(receipt, sort_keys=True) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix="refresh-receipt-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temporary, path)
        if path.read_bytes() != data:
            raise RuntimeError("Catalogue Refresh receipt did not verify")
        return receipt
    finally:
        temporary.unlink(missing_ok=True)


def refresh_catalogue(repo_root: Path) -> dict[str, Any]:
    """Refresh all owned Working readers, verify them, then record completion."""
    try:
        invalidate_refresh_receipt(repo_root)
        revision = _source_revision(repo_root)
        source_dir = repo_root / DEFAULT_SOURCE_DIR
        output = generate_catalogue_json(repo_root, source_dir, write=True)
        if not output["verified"]:
            raise RuntimeError("Catalogue JSON verification did not complete")
        records = records_from_json_source(source_dir)
        report = generate_catalogue_works_metadata(repo_root, records, write=True)
        titles = generate_works_collection_metadata(repo_root, records, write=True)
        if generate_catalogue_works_metadata(repo_root, records, write=False)["changed"]:
            raise RuntimeError("Catalogue Works report metadata did not verify")
        if generate_works_collection_metadata(repo_root, records, write=False)["changed"]:
            raise RuntimeError("Works collection metadata did not verify")
        receipt = _write_receipt(repo_root, revision)
        status = {"ok": True, "needed": False, "refreshed_at_utc": receipt["refreshed_at_utc"]}
        return {"ok": True, "output": output, "report_metadata": report,
                "works_collection_metadata": titles, "refresh_status": status}
    except Exception as error:
        try:
            invalidate_refresh_receipt(repo_root)
        except Exception as cleanup_error:
            raise RuntimeError(f"Refresh Catalogue incomplete: {error}; completion receipt could not be cleared: {cleanup_error}") from error
        raise RuntimeError(f"Refresh Catalogue incomplete: {error}") from error

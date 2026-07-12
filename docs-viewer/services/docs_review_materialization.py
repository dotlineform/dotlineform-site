#!/usr/bin/env python3
"""Atomic publication of persistent Docs Review packages."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable

from docs_review_build import build_review_package


def _safe_source_filename(value: Any) -> str:
    filename = str(value or "").strip()
    if not filename or Path(filename).name != filename or not filename.endswith(".md"):
        raise ValueError("review source filename must be a direct-child Markdown filename")
    return filename


def publish_review_package(
    repo_root: Path,
    *,
    package_path: Path,
    package_id: str,
    default_doc_id: str,
    source_records: Iterable[dict[str, Any]],
    manifest: dict[str, Any],
    asset_records: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build a complete package beside its final path, then publish it once."""

    if package_path.exists() or package_path.is_symlink():
        raise FileExistsError(f"review package already exists: {package_id}")
    package_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = Path(
        tempfile.mkdtemp(
            prefix=f".{package_id}.publishing-",
            dir=package_path.parent,
        )
    )
    try:
        sources = [dict(record) for record in source_records]
        source_dir = temporary_path / "source"
        source_dir.mkdir()
        for record in sources:
            filename = _safe_source_filename(record.get("filename"))
            source_text = record.get("source_text")
            if not isinstance(source_text, str):
                raise ValueError("review source_text must be a string")
            (source_dir / filename).write_text(source_text, encoding="utf-8")

        assets = [dict(record) for record in asset_records]
        build = build_review_package(
            repo_root,
            package_id=package_id,
            source_dir=source_dir,
            generated_dir=temporary_path / "generated",
            default_doc_id=default_doc_id,
            asset_records=assets,
        )
        if int(build.get("document_count") or 0) != len(sources):
            raise RuntimeError("review package generated document count does not match its source set")
        (temporary_path / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.rename(package_path)
        return build
    finally:
        if temporary_path.exists():
            shutil.rmtree(temporary_path)


__all__ = ["publish_review_package"]

from __future__ import annotations

from collections.abc import Collection, Mapping
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import quote

from .common import (
    FRONT_MATTER_PATTERN,
    humanize,
)
from docs_document_identity import is_document_id, is_immutable_doc_id
from docs_document_images import has_document_thumbnail
from docs_document_subjects import validate_document_subject_fields
from docs_front_matter import normalize_summary, read_front_matter_fields
from docs_index_order import read_index_order, tree_parent_ids
from docs_report_source import ReportDescriptor, ReportSourceContractRequired
from docs_source_model import (
    parse_document_report,
    report_source_contract_for_collection,
    validate_document_status_front_matter,
)


class FrontMatterSyntaxError(Exception):
    pass


class MissingDocIdError(Exception):
    pass


class InvalidDocIdError(Exception):
    pass


class DocumentIdentity(Protocol):
    """The saved identity is enough to resolve another document's membership."""

    @property
    def doc_id(self) -> str: ...

    @property
    def title(self) -> str: ...


@dataclass(frozen=True)
class DocRecord:
    doc_id: str
    title: str
    date: str
    date_display: str
    added_date: str
    last_updated: str
    summary: str
    ui_status: str
    parent_id: str
    source_path: str
    viewer_url: str
    content_url: str
    report: ReportDescriptor | None
    body_markdown: str
    source_text: str | None
    front_matter: dict[str, Any] = field(default_factory=dict)


def parse_source_text(raw: str, *, source_name: str) -> tuple[dict[str, Any], str]:
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        return {}, raw

    try:
        front_matter = {field.key: field.value for field in read_front_matter_fields(
            match.group(1), source_name=source_name, require_pairs=True,
        )}
        validate_document_subject_fields(front_matter)
    except ValueError as error:
        raise FrontMatterSyntaxError(f"problem with front-matter on doc {source_name}: {error}") from error
    return front_matter, raw[match.end() :]


def parse_source(path: Path) -> tuple[dict[str, Any], str]:
    return parse_source_text(
        path.read_text(encoding="utf-8"),
        source_name=path.as_posix(),
    )


def front_matter_boolean(front_matter: dict[str, Any], key: str, default: bool) -> bool:
    if key not in front_matter:
        return default
    value = front_matter[key]
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() not in {"false", "0", "no", "off"}


def extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"\A#\s+(.+?)\s*\Z", line.strip())
        if match:
            return match.group(1).strip()
    return ""


class SourceLoadingMixin:
    def load_docs(
        self, doc_ids: list[str] | None = None, *, parent_ids: dict[str, str] | None = None,
        capture_source_text: bool = False,
    ) -> list[DocRecord]:
        """Read all sources or only exact canonical filenames selected by ID."""
        if not self.source_dir.is_dir():
            raise FileNotFoundError(f"Docs source directory is unavailable: {self.source_dir}")
        ordinary = getattr(self, "collection_config", None) is None
        if parent_ids is None:
            parent_ids = tree_parent_ids(read_index_order(self.source_dir)) if ordinary else {}
        selected_ids = None if doc_ids is None else set(doc_ids)
        if ordinary:
            paths = []
            for doc_id in parent_ids:
                if not is_immutable_doc_id(doc_id):
                    raise InvalidDocIdError(f"Invalid document ID in index-order.json: {doc_id}")
                if selected_ids is None or doc_id in selected_ids:
                    path = self.source_dir / f"{doc_id}.md"
                    if path.is_symlink():
                        raise ValueError(f"Document source must not be a symlink: {path.name}")
                    paths.append(path)
        elif doc_ids is None:
            paths = sorted(self.source_dir.glob("**/*.md"))
        else:
            paths = []
            for doc_id in sorted(set(doc_ids)):
                if not is_document_id(doc_id, collection=getattr(self, "collection_id", "")):
                    raise InvalidDocIdError(f"Invalid selected document ID: {doc_id}")
                path = self.source_dir / f"{doc_id}.md"
                if path.is_symlink():
                    raise ValueError(f"Selected document source must not be a symlink: {path.name}")
                if path.is_file():
                    paths.append(path)
        self.source_files_scanned = len(paths)
        nested_paths = [path for path in paths if path.parent != self.source_dir]
        if nested_paths:
            nested = ", ".join(path.relative_to(self.source_dir).as_posix() for path in nested_paths)
            raise RuntimeError(f"Nested markdown docs are not supported under {self.source_dir}; move these files to the collection root: {nested}")

        docs: list[DocRecord] = []
        for path in paths:
            relative_path = path.relative_to(self.source_dir).as_posix()
            source_text = path.read_text(encoding="utf-8")
            front_matter, body_markdown = parse_source_text(
                source_text,
                source_name=relative_path,
            )
            stem = path.stem
            doc_id = str(front_matter.get("doc_id") or "").strip()
            if not doc_id:
                raise MissingDocIdError(f"Missing required doc_id in {relative_path}")
            if doc_id != path.stem:
                raise InvalidDocIdError(f"Selected source identity does not match its filename: {relative_path}")
            title = str(front_matter.get("title") or extract_title(body_markdown) or humanize(stem)).strip()
            parent_id = parent_ids[doc_id] if ordinary else ""
            date = str(front_matter.get("date") or "").strip()
            date_display = str(front_matter.get("date_display") or "").strip()
            last_updated = str(front_matter.get("last_updated") or "").strip()
            added_date = str(front_matter.get("added_date") or last_updated).strip()
            summary = normalize_summary(front_matter.get("summary"))
            ui_status = str(front_matter.get("ui_status") or "").strip()
            document_config = getattr(self, "collection_config", self.config)
            try:
                validate_document_status_front_matter(
                    front_matter,
                    collection_config=document_config,
                    source_name=relative_path,
                )
            except ValueError as exc:
                raise FrontMatterSyntaxError(str(exc)) from exc
            try:
                try:
                    report = parse_document_report(
                        source_text,
                        front_matter,
                        body_markdown,
                        source_name=relative_path,
                        contract=self.report_source_contract,
                    )
                except ReportSourceContractRequired:
                    self.report_source_contract = report_source_contract_for_collection(
                        self.repo_root,
                        self.config,
                        getattr(self, "collection_config", self.config),
                    )
                    report = parse_document_report(
                        source_text,
                        front_matter,
                        body_markdown,
                        source_name=relative_path,
                        contract=self.report_source_contract,
                    )
            except ValueError as exc:
                raise FrontMatterSyntaxError(str(exc)) from exc
            docs.append(
                DocRecord(
                    doc_id=doc_id,
                    title=title,
                    date=date,
                    date_display=date_display,
                    added_date=added_date,
                    last_updated=last_updated,
                    summary=summary,
                    ui_status=ui_status,
                    parent_id=parent_id,
                    source_path=relative_path,
                    viewer_url=self.viewer_url_for(doc_id),
                    content_url=self.content_url_for(doc_id),
                    report=report,
                    body_markdown=body_markdown,
                    source_text=source_text if capture_source_text else None,
                    front_matter=dict(front_matter),
                )
            )
        return docs

    def validate_canonical_doc_ids(self, docs: list[DocRecord]) -> None:
        for doc in docs:
            if not is_document_id(doc.doc_id, collection=getattr(self, "collection_id", "")):
                raise InvalidDocIdError(
                    f"doc_id must use the immutable document ID format in {doc.source_path}"
                )

    def validate_docs(self, docs: list[DocRecord], *, known_doc_ids: Collection[str] | None = None) -> None:
        by_id: dict[str, DocRecord] = {}
        duplicates: list[str] = []
        for doc in docs:
            if doc.doc_id in by_id:
                duplicates.append(doc.doc_id)
            by_id[doc.doc_id] = doc
        if duplicates:
            raise RuntimeError(f"Duplicate doc_id values: {', '.join(sorted(set(duplicates)))}")
        known_ids = by_id if known_doc_ids is None else known_doc_ids
        for doc in docs:
            if doc.parent_id and doc.parent_id not in known_ids and not self.allow_unresolved_parent_ids:
                raise RuntimeError(f"Unknown parent_id {doc.parent_id!r} for doc {doc.doc_id!r}")

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        pairs: list[str] = []
        pairs.append(f"doc={quote(str(doc_id))}")
        url = f"{self.viewer_base_url}?{'&'.join(pairs)}"
        return f"{url}#{anchor}" if anchor else url

    def content_url_for(self, doc_id: str) -> str:
        return f"/docs/doc?doc_id={quote(str(doc_id))}"

    def output_url_dir(self) -> Path:
        return self.output_dir

    def output_url_base_for(self, output_dir: Path) -> str:
        child = getattr(self, "collection_config", None)
        suffix = f"/{quote(child.collection)}" if child is not None else ""
        return f"/docs/generated/external{suffix}"

    def effective_parent_id(self, parent_id: str, known_doc_ids: Collection[str]) -> str:
        if not parent_id:
            return ""
        if parent_id in known_doc_ids:
            return parent_id
        return "" if self.allow_unresolved_parent_ids else parent_id

    def metadata_entry(self, doc: DocRecord, docs_by_id: Mapping[str, DocumentIdentity]) -> dict[str, Any]:
        entry = {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "added_date": doc.added_date,
            "last_updated": doc.last_updated,
            "viewer_url": doc.viewer_url,
        }
        if doc.date:
            entry["date"] = doc.date
        if doc.date_display:
            entry["date_display"] = doc.date_display
        parent_id = self.effective_parent_id(doc.parent_id, docs_by_id)
        if parent_id:
            entry["parent_id"] = parent_id
        if self.config.stage == "working" and getattr(self, "collection_id", "") != "catalogue":
            entry["draft"] = doc.front_matter["draft"]
        if doc.summary:
            entry["summary"] = doc.summary
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
        return entry

    def reader_metadata_entry(self, doc: DocRecord) -> dict[str, Any]:
        entry = {
            "title": doc.title,
            "last_updated": doc.last_updated,
        }
        if doc.date:
            entry["date"] = doc.date
        if doc.date_display:
            entry["date_display"] = doc.date_display
        if doc.summary:
            entry["summary"] = doc.summary
        return entry

    def by_id_metadata_entry(self, doc: DocRecord, docs_by_id: Mapping[str, DocumentIdentity]) -> dict[str, Any]:
        entry = self.metadata_entry(doc, docs_by_id)
        del entry["viewer_url"]
        if has_document_thumbnail(doc.front_matter, collection=getattr(self, "collection_id", "")):
            entry["has_thumbnail"] = True
        if doc.report is not None:
            entry["report"] = dict(doc.report.as_payload())
        return entry

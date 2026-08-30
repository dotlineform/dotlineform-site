from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .common import (
    FRONT_MATTER_PATTERN,
    INTEGER_PATTERN,
    browser_path_for_repo_relative,
    humanize,
    normalize_text,
    plain_text_from_html,
    publication_documents_path,
    read_json,
    scope_uses_external_data,
)
from docs_document_identity import is_immutable_doc_id
from docs_report_source import ReportDescriptor, ReportSourceContractRequired
from docs_source_model import (
    parse_document_report,
    report_source_contract_for_collection,
    validate_publishable_front_matter,
)


class FrontMatterSyntaxError(Exception):
    pass


class MissingDocIdError(Exception):
    pass


class InvalidDocIdError(Exception):
    pass


@dataclass(frozen=True)
class DocRecord:
    scope_id: str
    doc_id: str
    title: str
    date: str
    date_display: str
    added_date: str
    last_updated: str
    summary: str
    ui_status: str
    parent_id: str
    publishable: bool
    source_path: str
    viewer_url: str
    content_url: str
    report: ReportDescriptor | None
    body_markdown: str
    group: str = ""
    front_matter: dict[str, Any] = field(default_factory=dict)
def parse_front_matter_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value == '""':
        return ""
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if INTEGER_PATTERN.fullmatch(value):
        try:
            return int(value)
        except ValueError:
            return value
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        if value[0] == '"':
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, str) else value[1:-1]
            except json.JSONDecodeError:
                return value[1:-1]
        return value[1:-1].replace("\\'", "'")
    return value


def parse_source_text(raw: str, *, source_name: str) -> tuple[dict[str, Any], str]:
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        return {}, raw

    front_matter: dict[str, Any] = {}
    for index, line in enumerate(match.group(1).splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise FrontMatterSyntaxError(f"problem with front-matter on doc {source_name} at line {index}: expected key: value")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise FrontMatterSyntaxError(f"problem with front-matter on doc {source_name} at line {index}: empty key")
        front_matter[key] = parse_front_matter_value(value)
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
    def load_docs(self) -> list[DocRecord]:
        paths = sorted(self.source_dir.glob("**/*.md"))
        self.source_files_scanned = len(paths)
        nested_paths = [path for path in paths if path.parent != self.source_dir]
        if nested_paths:
            nested = ", ".join(path.relative_to(self.source_dir).as_posix() for path in nested_paths)
            raise RuntimeError(f"Nested markdown docs are not supported under {self.source_dir}; move these files to the scope root: {nested}")

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
            title = str(front_matter.get("title") or extract_title(body_markdown) or humanize(stem)).strip()
            parent_id = str(front_matter.get("parent_id") if "parent_id" in front_matter else "").strip()
            date = str(front_matter.get("date") or "").strip()
            date_display = str(front_matter.get("date_display") or "").strip()
            last_updated = str(front_matter.get("last_updated") or "").strip()
            added_date = str(front_matter.get("added_date") or last_updated).strip()
            summary = normalize_text(front_matter.get("summary"))
            ui_status = str(front_matter.get("ui_status") or "").strip()
            raw_group = front_matter.get("group")
            if raw_group is not None and not isinstance(raw_group, str):
                raise FrontMatterSyntaxError(
                    f"group must be a scalar string in {relative_path}"
                )
            group = str(raw_group or "").strip().lower()
            document_config = getattr(self, "sub_scope_config", self.config)
            try:
                validate_publishable_front_matter(
                    front_matter,
                    collection_config=document_config,
                    source_name=relative_path,
                )
            except ValueError as exc:
                raise FrontMatterSyntaxError(str(exc)) from exc
            publishable = front_matter_boolean(front_matter, "publishable", True)
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
                        getattr(self, "sub_scope_config", self.config),
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
                    scope_id=self.scope_id,
                    doc_id=doc_id,
                    title=title,
                    date=date,
                    date_display=date_display,
                    added_date=added_date,
                    last_updated=last_updated,
                    summary=summary,
                    ui_status=ui_status,
                    parent_id=parent_id,
                    publishable=publishable,
                    source_path=relative_path,
                    viewer_url=self.viewer_url_for(doc_id),
                    content_url=self.content_url_for(doc_id),
                    report=report,
                    body_markdown=body_markdown,
                    group=group,
                    front_matter=dict(front_matter),
                )
            )
        return docs

    def validate_canonical_doc_ids(self, docs: list[DocRecord]) -> None:
        for doc in docs:
            if not is_immutable_doc_id(doc.doc_id):
                raise InvalidDocIdError(
                    f"doc_id must use the immutable document ID format in {doc.source_path}"
                )

    def validate_docs(self, docs: list[DocRecord]) -> None:
        by_id: dict[str, DocRecord] = {}
        duplicates: list[str] = []
        for doc in docs:
            if doc.doc_id in by_id:
                duplicates.append(doc.doc_id)
            by_id[doc.doc_id] = doc
        if duplicates:
            raise RuntimeError(f"Duplicate doc_id values: {', '.join(sorted(set(duplicates)))}")
        for doc in docs:
            if doc.parent_id and doc.parent_id not in by_id and not self.allow_unresolved_parent_ids:
                raise RuntimeError(f"Unknown parent_id {doc.parent_id!r} for doc {doc.doc_id!r}")

    def validate_targeted_build_prerequisites(self, docs: list[DocRecord], target_doc_ids: list[str]) -> None:
        if not (self.output_dir / "index-tree.json").exists():
            raise RuntimeError("Targeted docs build requires existing scope index tree; run a full-scope build first")
        if not (self.semantic_tokens_dir / "index.json").exists():
            raise RuntimeError(
                "Targeted docs build requires existing semantic-token index; "
                "run a full-scope build first"
            )
        missing = [
            doc.doc_id for doc in docs
            if doc.doc_id not in target_doc_ids and not (self.items_dir / f"{doc.doc_id}.json").exists()
        ]
        if missing:
            raise RuntimeError(
                "Targeted docs build requires existing payloads for unselected docs; "
                f"run a full-scope build first: {', '.join(missing)}"
            )

    def viewer_url_for(self, doc_id: str, anchor: str = "") -> str:
        pairs: list[str] = []
        if self.include_scope_param and self.scope_id:
            pairs.append(f"scope={quote(self.scope_id)}")
        pairs.append(f"doc={quote(str(doc_id))}")
        url = f"{self.viewer_base_url}?{'&'.join(pairs)}"
        return f"{url}#{anchor}" if anchor else url

    def content_url_for(self, doc_id: str) -> str:
        if scope_uses_external_data(self.config):
            return f"/docs/doc?scope={quote(self.scope_id)}&doc_id={quote(str(doc_id))}"
        return f"{self.output_url_base}/by-id/{quote(str(doc_id))}.json"

    def output_url_dir(self) -> Path:
        if self.public_readonly_scope:
            return self.repo_root / publication_documents_path(self.config)
        return self.output_dir

    def output_url_base_for(self, output_dir: Path) -> str:
        if scope_uses_external_data(self.config):
            return f"/docs/generated/external/{quote(self.scope_id)}"
        try:
            relative = output_dir.resolve().relative_to(self.repo_root)
        except ValueError as exc:
            raise RuntimeError(f"Docs output path must be inside the repo root: {output_dir}") from exc
        return browser_path_for_repo_relative(relative)

    def effective_parent_id(self, doc: DocRecord, docs: list[DocRecord]) -> str:
        if not doc.parent_id:
            return ""
        if any(candidate.doc_id == doc.parent_id for candidate in docs):
            return doc.parent_id
        return "" if self.allow_unresolved_parent_ids else doc.parent_id

    def metadata_entry(self, doc: DocRecord, docs: list[DocRecord]) -> dict[str, Any]:
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
        parent_id = self.effective_parent_id(doc, docs)
        if parent_id:
            entry["parent_id"] = parent_id
        if not doc.publishable:
            entry["publishable"] = False
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

    def by_id_metadata_entry(self, doc: DocRecord, docs: list[DocRecord]) -> dict[str, Any]:
        entry = (
            self.reader_metadata_entry(doc)
            if self.public_readonly_scope
            else self.metadata_entry(doc, docs)
        )
        if doc.report is not None:
            entry["report"] = dict(doc.report.as_payload())
        return entry

    def index_entry(self, doc: DocRecord, docs: list[DocRecord], item_payload: dict[str, Any] | None) -> dict[str, Any]:
        item = item_payload if item_payload is not None else read_json(self.items_dir / f"{doc.doc_id}.json")
        entry = self.metadata_entry(doc, docs)
        entry["content_url"] = doc.content_url
        entry["content_text_length"] = len(plain_text_from_html((item or {}).get("content_html", ""), title=doc.title))
        return entry

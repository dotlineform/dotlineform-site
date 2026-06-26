from __future__ import annotations

import json
from dataclasses import dataclass
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
    read_json,
    resolve_scope_path,
    scope_uses_external_data,
    path_is_under_configured_sub_scope_source,
)


class FrontMatterSyntaxError(Exception):
    pass


class MissingDocIdError(Exception):
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
    viewable: bool
    source_path: str
    viewer_url: str
    content_url: str
    viewer_report: str
    viewer_report_scope: str
    viewer_report_access: str
    viewer_report_preset: str
    viewer_report_subscope: str
    body_markdown: str
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


def parse_source(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_PATTERN.match(raw)
    if not match:
        return {}, raw

    front_matter: dict[str, Any] = {}
    for index, line in enumerate(match.group(1).splitlines(), start=2):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            rel = path.as_posix()
            raise FrontMatterSyntaxError(f"problem with front-matter on doc {rel} at line {index}: expected key: value")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if not key:
            rel = path.as_posix()
            raise FrontMatterSyntaxError(f"problem with front-matter on doc {rel} at line {index}: empty key")
        front_matter[key] = parse_front_matter_value(value)
    return front_matter, raw[match.end() :]


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
        paths = [
            path for path in sorted(self.source_dir.glob("**/*.md"))
            if not path_is_under_configured_sub_scope_source(path, self.source_dir, self.config)
        ]
        self.source_files_scanned = len(paths)
        nested_paths = [path for path in paths if path.parent != self.source_dir]
        if nested_paths:
            nested = ", ".join(path.relative_to(self.source_dir).as_posix() for path in nested_paths)
            raise RuntimeError(f"Nested markdown docs are not supported under {self.source_dir}; move these files to the scope root: {nested}")

        docs: list[DocRecord] = []
        for path in paths:
            relative_path = path.relative_to(self.source_dir).as_posix()
            front_matter, body_markdown = parse_source(path)
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
            viewable = front_matter_boolean(front_matter, "viewable", True)
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
                    viewable=viewable,
                    source_path=relative_path,
                    viewer_url=self.viewer_url_for(doc_id),
                    content_url=self.content_url_for(doc_id),
                    viewer_report=str(front_matter.get("viewer_report") or "").strip(),
                    viewer_report_scope=str(front_matter.get("viewer_report_scope") or "").strip(),
                    viewer_report_access=str(front_matter.get("viewer_report_access") or "").strip(),
                    viewer_report_preset=str(front_matter.get("viewer_report_preset") or "").strip(),
                    viewer_report_subscope=str(front_matter.get("viewer_report_subscope") or "").strip(),
                    body_markdown=body_markdown,
                )
            )
        return docs

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
        if not (self.references_dir / "index.json").exists():
            raise RuntimeError("Targeted docs build requires existing references index; run a full-scope build first")
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
            return f"/docs/generated/payload?scope={quote(self.scope_id)}&doc_id={quote(str(doc_id))}"
        return f"{self.output_url_base}/by-id/{quote(str(doc_id))}.json"

    def output_url_dir(self) -> Path:
        if self.public_readonly_scope:
            return self.repo_root / self.config.publish_output
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
            "source_path": doc.source_path,
            "viewer_url": doc.viewer_url,
        }
        if doc.date:
            entry["date"] = doc.date
        if doc.date_display:
            entry["date_display"] = doc.date_display
        parent_id = self.effective_parent_id(doc, docs)
        if parent_id:
            entry["parent_id"] = parent_id
        if not doc.viewable:
            entry["viewable"] = False
        if doc.summary:
            entry["summary"] = doc.summary
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
        for key in (
            "viewer_report",
            "viewer_report_scope",
            "viewer_report_access",
            "viewer_report_preset",
            "viewer_report_subscope",
        ):
            value = getattr(doc, key)
            if value:
                entry[key] = value
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
        if doc.viewer_report and doc.viewer_report_access == "public":
            entry["viewer_report"] = doc.viewer_report
            entry["viewer_report_access"] = doc.viewer_report_access
            if doc.viewer_report_scope:
                entry["viewer_report_scope"] = doc.viewer_report_scope
            if doc.viewer_report_preset:
                entry["viewer_report_preset"] = doc.viewer_report_preset
            if doc.viewer_report_subscope:
                entry["viewer_report_subscope"] = doc.viewer_report_subscope
        return entry

    def by_id_metadata_entry(self, doc: DocRecord, docs: list[DocRecord]) -> dict[str, Any]:
        if self.public_readonly_scope:
            return self.reader_metadata_entry(doc)
        return self.metadata_entry(doc, docs)

    def index_entry(self, doc: DocRecord, docs: list[DocRecord], item_payload: dict[str, Any] | None) -> dict[str, Any]:
        item = item_payload if item_payload is not None else read_json(self.items_dir / f"{doc.doc_id}.json")
        entry = self.metadata_entry(doc, docs)
        entry["content_url"] = doc.content_url
        entry["content_text_length"] = len(plain_text_from_html((item or {}).get("content_html", ""), title=doc.title))
        return entry

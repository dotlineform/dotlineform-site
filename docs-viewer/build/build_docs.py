#!/usr/bin/env python3
"""Build Docs Viewer generated document payloads without Ruby/Jekyll."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse


REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_SERVICES_DIR = REPO_ROOT / "docs-viewer" / "services"
SHARED_PYTHON_DIR = REPO_ROOT / "studio" / "shared" / "python"
for path in (DOCS_SERVICES_DIR, SHARED_PYTHON_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from docs_scope_config import (  # noqa: E402
    CONFIG_REL_PATH,
    DocsScopeConfig,
    is_public_readonly_scope,
    load_docs_scope_configs,
    normalize_viewer_base_url,
)
from markdown_renderer import plain_text_from_html, render_markdown_to_html  # noqa: E402


DOCS_VIEWER_BROWSER_CONFIG_PATH = Path("docs-viewer/config/defaults/docs-viewer-config.json")
DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH = Path("docs-viewer/config/defaults/docs-viewer-public-config.json")
DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION = "docs_viewer_config_v1"
FRONT_MATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
MEDIA_TOKEN_PATTERN = re.compile(r"\[\[media:(.+?)\]\]")
INTERACTIVE_HTML_TOKEN_PATTERN = re.compile(r"\[\[interactive-html:(.+?)\]\]")
SEMANTIC_REF_TOKEN_PATTERN = re.compile(r"\[\[ref:(.*?)\]\](\{[^}\n]*\})?", re.DOTALL)
INTERACTIVE_HTML_FILENAME_PATTERN = re.compile(r"\A[a-z0-9][a-z0-9._-]*\.html\Z", re.IGNORECASE)
INTERACTIVE_HTML_HEIGHT_PATTERN = re.compile(r"\A[1-9][0-9]{0,3}\Z")
IMG_PATTERN = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
HTML_ATTR_PATTERN_TEMPLATE = r"\b{}\s*=\s*([\"'])(.*?)\1"
INTEGER_PATTERN = re.compile(r"^-?\d+$")
SAFE_REF_KIND_PATTERN = re.compile(r"\A[a-z0-9_-]+\Z")
SEMANTIC_REF_ALLOWED_ACTIONS = {"link"}
SEMANTIC_REF_SUPPORTED_KINDS = {"work", "series", "moment"}


class FrontMatterSyntaxError(Exception):
    pass


@dataclass(frozen=True)
class DocRecord:
    scope_id: str
    doc_id: str
    title: str
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
    body_markdown: str


@dataclass(frozen=True)
class SemanticRefToken:
    raw: str
    kind: str
    id: str
    label: str
    action: str
    modifier_error: str


def monotonic_time() -> float:
    return time.perf_counter()


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


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


def humanize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[_\-\s]+", value.strip()) if part)


def html_attr(raw_attrs: str, name: str) -> str:
    pattern = re.compile(HTML_ATTR_PATTERN_TEMPLATE.format(re.escape(name)), re.IGNORECASE | re.DOTALL)
    match = pattern.search(raw_attrs or "")
    return match.group(2) if match else ""


def add_missing_image_titles(content_html: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw_attrs = match.group(1) or ""
        alt = html_attr(raw_attrs, "alt").strip()
        title = html_attr(raw_attrs, "title").strip()
        if not alt or title:
            return match.group(0)
        attrs = re.sub(r"\s*/\s*\Z", "", raw_attrs)
        closing = " /" if re.search(r"\s*/\s*\Z", raw_attrs) else ""
        return f'<img{attrs} title="{html.escape(html.unescape(alt), quote=True)}"{closing}>'

    return IMG_PATTERN.sub(replace, content_html or "")


def json_text(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_simple_yaml_scalars(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        value = str(parse_front_matter_value(raw_value))
        values[key.strip()] = value.strip()
    return values


def normalize_doc_ids(values: list[str] | tuple[str, ...] | None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values or []:
        doc_id = str(value or "").strip()
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            result.append(doc_id)
    return sorted(result)


class DocsDataBuilder:
    def __init__(
        self,
        *,
        repo_root: Path,
        config: DocsScopeConfig,
        source_dir: Path | None = None,
        output_dir: Path | None = None,
        viewer_base_url: str | None = None,
        only_doc_ids: list[str] | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.scope_id = config.scope_id
        self.source_dir = (self.repo_root / (source_dir or config.source)).resolve()
        self.output_dir = (self.repo_root / (output_dir or config.output)).resolve()
        self.items_dir = self.output_dir / "by-id"
        self.viewer_base_url = normalize_viewer_base_url(viewer_base_url or config.viewer_base_url)
        self.include_scope_param = config.include_scope_param
        self.allow_nested_source = config.allow_nested_source
        self.non_loadable_doc_ids = normalize_doc_ids(list(config.non_loadable_doc_ids))
        self.manage_only_tree_root_ids = normalize_doc_ids(list(config.manage_only_tree_root_ids))
        self.show_updated_date = config.show_updated_date is not False
        self.allow_unresolved_parent_ids = config.allow_unresolved_parent_ids is True
        self.only_doc_ids = None if only_doc_ids is None else normalize_doc_ids(only_doc_ids)
        self.output_url_base = self.output_url_base_for(self.output_dir)
        self.site_config = load_simple_yaml_scalars(self.repo_root / "_config.yml")
        self.source_files_scanned = 0
        self.warnings: list[str] = []
        self._catalogue_cache: dict[str, dict[str, dict[str, Any]]] = {}
        self._viewer_scope_for_path: dict[str, str] | None = None

    def run(self, *, write: bool, emit_diagnostics: bool = False) -> dict[str, Any]:
        started_at = monotonic_time()
        docs = self.load_docs()
        self.validate_docs(docs)
        target_doc_ids = self.only_doc_ids if self.only_doc_ids is not None else [doc.doc_id for doc in docs]
        if self.targeted_build:
            self.validate_targeted_build_prerequisites(docs, target_doc_ids)
            semantic_references_by_doc = self.existing_reference_records_by_doc(docs, target_doc_ids)
        else:
            semantic_references_by_doc: dict[str, list[dict[str, Any]]] = {}

        docs_for_item_build = [doc for doc in docs if doc.doc_id in target_doc_ids]
        item_payloads = {
            doc.doc_id: self.item_entry(doc, docs, semantic_references_by_doc) for doc in docs_for_item_build
        }
        for doc in docs_for_item_build:
            semantic_references_by_doc.setdefault(doc.doc_id, [])

        docs_index = [
            self.index_entry(doc, docs, item_payloads.get(doc.doc_id)) for doc in self.ordered_docs_for_index(docs)
        ]
        viewer_options = self.viewer_options_payload()
        index_payload = {
            "generated_at": self.effective_generated_at(docs_index, viewer_options),
            "viewer_options": viewer_options,
            "docs": docs_index,
        }
        reference_payloads = self.build_reference_payloads(docs, semantic_references_by_doc)
        write_plan = self.build_write_plan(
            index_payload,
            item_payloads,
            reference_payloads,
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        diagnostics = self.diagnostics_payload(
            docs=docs,
            write_plan=write_plan,
            elapsed_seconds=round(monotonic_time() - started_at, 3),
            target_doc_ids=target_doc_ids if self.targeted_build else None,
        )
        if write:
            self.write_outputs(
                write_plan,
                docs_total=len(index_payload["docs"]),
                reference_total=reference_payloads["index"]["header"]["count"],
            )
        else:
            self.print_dry_run(index_payload, reference_payloads, write_plan)
        if emit_diagnostics:
            self.print_diagnostics(diagnostics)
        return {
            "index_payload": index_payload,
            "item_payloads": item_payloads,
            "reference_payloads": reference_payloads,
            "write_plan": write_plan,
            "diagnostics": diagnostics,
        }

    @property
    def targeted_build(self) -> bool:
        return self.only_doc_ids is not None

    def viewer_options_payload(self) -> dict[str, Any]:
        return {
            "non_loadable_doc_ids": self.non_loadable_doc_ids,
            "manage_only_tree_root_ids": self.manage_only_tree_root_ids,
            "show_updated_date": self.show_updated_date,
        }

    def load_docs(self) -> list[DocRecord]:
        paths = sorted(self.source_dir.glob("**/*.md"))
        self.source_files_scanned = len(paths)
        nested_paths = [path for path in paths if path.parent != self.source_dir]
        if nested_paths and not self.allow_nested_source:
            nested = ", ".join(path.relative_to(self.source_dir).as_posix() for path in nested_paths)
            raise RuntimeError(f"Nested markdown docs are not supported under {self.source_dir}; move these files to the scope root: {nested}")

        docs: list[DocRecord] = []
        for path in paths:
            relative_path = path.relative_to(self.source_dir).as_posix()
            front_matter, body_markdown = parse_source(path)
            stem = path.stem
            doc_id = str(front_matter.get("doc_id") or stem).strip()
            title = str(front_matter.get("title") or extract_title(body_markdown) or humanize(stem)).strip()
            parent_id = str(front_matter.get("parent_id") if "parent_id" in front_matter else "").strip()
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
        if not (self.output_dir / "index.json").exists():
            raise RuntimeError("Targeted docs build requires existing scope index; run a full-scope build first")
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
        return f"{self.output_url_base}/by-id/{quote(str(doc_id))}.json"

    def output_url_base_for(self, output_dir: Path) -> str:
        try:
            relative = output_dir.resolve().relative_to(self.repo_root)
        except ValueError as exc:
            raise RuntimeError(f"Docs output path must be inside the repo root: {output_dir}") from exc
        return f"/{relative.as_posix()}"

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
        parent_id = self.effective_parent_id(doc, docs)
        if parent_id:
            entry["parent_id"] = parent_id
        if not doc.viewable:
            entry["viewable"] = False
        if doc.summary:
            entry["summary"] = doc.summary
        if doc.ui_status:
            entry["ui_status"] = doc.ui_status
        for key in ("viewer_report", "viewer_report_scope", "viewer_report_access", "viewer_report_preset"):
            value = getattr(doc, key)
            if value:
                entry[key] = value
        return entry

    def index_entry(self, doc: DocRecord, docs: list[DocRecord], item_payload: dict[str, Any] | None) -> dict[str, Any]:
        item = item_payload if item_payload is not None else read_json(self.items_dir / f"{doc.doc_id}.json")
        entry = self.metadata_entry(doc, docs)
        entry["content_url"] = doc.content_url
        entry["content_text_length"] = len(plain_text_from_html((item or {}).get("content_html", ""), title=doc.title))
        return entry

    def item_entry(
        self,
        doc: DocRecord,
        docs: list[DocRecord],
        semantic_references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        resolved = self.resolve_content_tokens(doc.body_markdown, doc=doc, references_by_doc=semantic_references_by_doc)
        content_html = add_missing_image_titles(
            self.rewrite_doc_links(render_markdown_to_html(resolved), current_doc=doc, docs=docs)
        )
        entry = self.metadata_entry(doc, docs)
        entry["content_html"] = content_html
        return entry

    def doc_sort_key(self, doc: DocRecord) -> tuple[str, str]:
        return (doc.title.lower(), doc.doc_id)

    def ordered_docs_for_index(self, docs: list[DocRecord]) -> list[DocRecord]:
        children_by_parent: dict[str, list[DocRecord]] = {}
        for doc in docs:
            children_by_parent.setdefault(self.effective_parent_id(doc, docs), []).append(doc)
        for children in children_by_parent.values():
            children.sort(key=self.doc_sort_key)
        ordered: list[DocRecord] = []
        seen: set[str] = set()

        def append_children(parent_id: str) -> None:
            for child in children_by_parent.get(parent_id, []):
                if child.doc_id in seen:
                    continue
                seen.add(child.doc_id)
                ordered.append(child)
                append_children(child.doc_id)

        append_children("")
        for doc in sorted(docs, key=self.doc_sort_key):
            if doc.doc_id not in seen:
                seen.add(doc.doc_id)
                ordered.append(doc)
        return ordered

    def effective_generated_at(self, docs_index: list[dict[str, Any]], viewer_options: dict[str, Any]) -> str:
        existing = read_json(self.output_dir / "index.json")
        if not isinstance(existing, dict):
            return utc_timestamp()
        if existing.get("docs") == docs_index and existing.get("viewer_options") == viewer_options:
            existing_generated_at = str(existing.get("generated_at") or "").strip()
            if existing_generated_at:
                return existing_generated_at
        return utc_timestamp()

    def rewrite_doc_links(self, content_html: str, *, current_doc: DocRecord, docs: list[DocRecord]) -> str:
        docs_by_id = {doc.doc_id: doc for doc in docs}
        docs_by_source = {doc.source_path: doc for doc in docs}
        docs_by_repo_path = {
            (self.source_dir / doc.source_path).resolve().as_posix(): doc for doc in docs
        }

        def replace(match: re.Match[str]) -> str:
            quote_char = match.group(1)
            href = match.group(2)
            rewritten = self.rewrite_href(
                href,
                current_doc=current_doc,
                docs_by_id=docs_by_id,
                docs_by_source=docs_by_source,
                docs_by_repo_path=docs_by_repo_path,
            )
            return f"href={quote_char}{rewritten}{quote_char}"

        return re.sub(r"href=([\"'])(.*?)\1", replace, content_html)

    def rewrite_href(
        self,
        href: str,
        *,
        current_doc: DocRecord,
        docs_by_id: dict[str, DocRecord],
        docs_by_source: dict[str, DocRecord],
        docs_by_repo_path: dict[str, DocRecord],
    ) -> str:
        if not href or href.startswith(("#", "mailto:")) or re.match(r"\A[a-z][a-z0-9+\-.]*:", href, re.IGNORECASE):
            return href
        parsed = urlparse(href)
        path_part = parsed.path or ""
        if not path_part:
            return href
        query_values = parse_qs(parsed.query)
        viewer_doc_id = (query_values.get("doc") or [""])[0]
        if viewer_doc_id and self.viewer_path_match(path_part, query_values):
            target = docs_by_id.get(viewer_doc_id)
            return self.viewer_url_for(target.doc_id, parsed.fragment) if target else href
        if path_part.startswith(self.repo_root.as_posix()):
            target = docs_by_repo_path.get(Path(path_part).resolve().as_posix())
            return self.viewer_url_for(target.doc_id, parsed.fragment) if target else href
        if not path_part.endswith(".md"):
            return href
        resolved = (Path(current_doc.source_path).parent / path_part).as_posix()
        normalized = Path(resolved).as_posix()
        target = docs_by_source.get(normalized)
        return self.viewer_url_for(target.doc_id, parsed.fragment) if target else href

    def viewer_path_match(self, path_part: str, query_values: dict[str, list[str]]) -> bool:
        explicit_scope = (query_values.get("scope") or [""])[0]
        if explicit_scope and explicit_scope != self.scope_id:
            return False
        if normalize_viewer_base_url(path_part) == self.viewer_base_url:
            return True
        return self.viewer_scope_for_path().get(normalize_viewer_base_url(path_part), "") == self.scope_id

    def viewer_scope_for_path(self) -> dict[str, str]:
        if self._viewer_scope_for_path is None:
            configs = load_docs_scope_configs(self.repo_root)
            self._viewer_scope_for_path = {
                normalize_viewer_base_url(config.viewer_base_url): scope_id for scope_id, config in configs.items()
            }
        return self._viewer_scope_for_path

    def resolve_content_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        resolved = self.resolve_interactive_html_tokens(self.resolve_media_tokens(markdown))
        return self.resolve_semantic_ref_tokens(resolved, doc=doc, references_by_doc=references_by_doc)

    def resolve_media_tokens(self, markdown: str) -> str:
        if "[[media:" not in markdown:
            return markdown
        return MEDIA_TOKEN_PATTERN.sub(lambda match: self.resolve_media_url(match.group(1)), markdown)

    def resolve_media_url(self, raw_path: str) -> str:
        relative_path = raw_path.strip()
        if not relative_path:
            return ""
        if re.match(r"\A[a-z][a-z0-9+\-.]*://", relative_path, re.IGNORECASE):
            return relative_path
        clean_path = relative_path.lstrip("/")
        media_base = str(self.site_config.get("media_base") or "").strip()
        return f"/{clean_path}" if not media_base else f"{media_base.rstrip('/')}/{clean_path}"

    def resolve_interactive_html_tokens(self, markdown: str) -> str:
        if "[[interactive-html:" not in markdown:
            return markdown
        return INTERACTIVE_HTML_TOKEN_PATTERN.sub(lambda match: self.interactive_html_iframe(match.group(1)), markdown)

    def interactive_html_iframe(self, raw_body: str) -> str:
        token = self.parse_interactive_html_token(raw_body)
        filename = token["filename"]
        asset_path = self.repo_root / self.interactive_html_asset_relative_path(filename)
        if not asset_path.exists():
            raise RuntimeError(
                f"Interactive HTML asset not found for scope {self.scope_id}: "
                f"{self.interactive_html_asset_relative_path(filename)}"
            )
        public_path = f"/assets/docs/interactive/{self.scope_id}/{filename}"
        title = f"Interactive HTML: {filename}"
        style_attr = f' style="--docs-viewer-interactive-height: {token["height"]}px"' if token.get("height") else ""
        return (
            f'<iframe class="docsViewer__interactiveFrame" src="{html.escape(public_path, quote=True)}" '
            f'sandbox="allow-scripts" loading="lazy" title="{html.escape(title, quote=True)}"{style_attr}></iframe>'
        )

    def parse_interactive_html_token(self, raw_body: str) -> dict[str, Any]:
        parts = raw_body.strip().split()
        filename = parts.pop(0) if parts else ""
        if not INTERACTIVE_HTML_FILENAME_PATTERN.fullmatch(filename):
            raise RuntimeError(f"Invalid interactive HTML token {filename!r}; use a same-scope .html filename only")
        token: dict[str, Any] = {"filename": filename}
        for part in parts:
            key, _, value = part.partition("=")
            if key != "height":
                raise RuntimeError(f"Invalid interactive HTML token attribute {part!r}; supported attributes: height")
            if not INTERACTIVE_HTML_HEIGHT_PATTERN.fullmatch(value):
                raise RuntimeError(f"Invalid interactive HTML token height in {raw_body!r}; use height=<positive pixel integer>")
            token["height"] = int(value)
        return token

    def interactive_html_asset_relative_path(self, filename: str) -> Path:
        return Path("assets/docs/interactive") / self.scope_id / filename

    def resolve_semantic_ref_tokens(
        self,
        markdown: str,
        *,
        doc: DocRecord,
        references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> str:
        if "[[ref:" not in markdown:
            references_by_doc[doc.doc_id] = []
            return markdown
        references: list[dict[str, Any]] = []
        ordinal = 0

        def replace_token(raw_token: str, raw_body: str, raw_modifier: str) -> str:
            nonlocal ordinal
            ordinal += 1
            token = self.parse_semantic_ref_token(raw_token, raw_body, raw_modifier)
            if token is None:
                self.warn_semantic_ref(doc, f"malformed semantic reference token {raw_token!r}")
                return f'<span data-ref-status="malformed">{html.escape(raw_token)}</span>'
            resolution = self.resolve_semantic_ref(token)
            warnings = self.semantic_ref_warnings(token, resolution)
            for message in warnings:
                self.warn_semantic_ref(doc, message)
            references.append(self.semantic_ref_record(doc, token, resolution, ordinal))
            return self.render_semantic_ref_token(token, resolution, not warnings)

        rendered = self.replace_semantic_ref_tokens_outside_code(markdown, replace_token)
        references_by_doc[doc.doc_id] = references
        return rendered

    def replace_semantic_ref_tokens_outside_code(self, markdown: str, replacer: Any) -> str:
        output: list[str] = []
        in_fence = False
        fence_marker = ""
        for line in markdown.splitlines(keepends=True):
            fence_match = re.match(r"\A {0,3}(`{3,}|~{3,})", line)
            if fence_match:
                marker = fence_match.group(1)
                if in_fence and marker.startswith(fence_marker):
                    in_fence = False
                    fence_marker = ""
                elif not in_fence:
                    in_fence = True
                    fence_marker = marker[0]
                output.append(line)
                continue
            output.append(line if in_fence else self.replace_semantic_ref_tokens_outside_inline_code(line, replacer))
        return "".join(output)

    def replace_semantic_ref_tokens_outside_inline_code(self, line: str, replacer: Any) -> str:
        output: list[str] = []
        index = 0
        while index < len(line):
            tick_match = re.search(r"`+", line[index:])
            segment_end = index + tick_match.start(0) if tick_match else len(line)
            output.append(self.replace_semantic_ref_tokens_in_text(line[index:segment_end], replacer))
            if not tick_match:
                break
            tick_start = index + tick_match.start(0)
            tick_end = index + tick_match.end(0)
            tick = tick_match.group(0)
            close_index = line.find(tick, tick_end)
            if close_index >= 0:
                output.append(line[tick_start:close_index + len(tick)])
                index = close_index + len(tick)
            else:
                output.append(line[tick_start:])
                index = len(line)
        return "".join(output)

    def replace_semantic_ref_tokens_in_text(self, text: str, replacer: Any) -> str:
        def replace(match: re.Match[str]) -> str:
            return replacer(match.group(0), match.group(1), match.group(2) or "")

        return SEMANTIC_REF_TOKEN_PATTERN.sub(replace, text)

    def parse_semantic_ref_token(self, raw_token: str, raw_body: str, raw_modifier: str) -> SemanticRefToken | None:
        target, _, explicit_label = raw_body.partition("|")
        kind, sep, target_id = target.partition(":")
        kind = kind.strip().lower()
        target_id = target_id.strip()
        if not sep or not kind or not target_id or not SAFE_REF_KIND_PATTERN.fullmatch(kind):
            return None
        modifier = self.parse_semantic_ref_modifier(raw_modifier)
        return SemanticRefToken(
            raw=raw_token,
            kind=kind,
            id=target_id,
            label=explicit_label.strip(),
            action=modifier.get("action", "link"),
            modifier_error=modifier.get("error", ""),
        )

    def parse_semantic_ref_modifier(self, raw_modifier: str) -> dict[str, str]:
        if not raw_modifier.strip():
            return {"action": "link"}
        inner = raw_modifier.strip().removeprefix("{").removesuffix("}").strip()
        if not inner:
            return {"action": "link", "error": "empty modifier"}
        attrs: dict[str, str] = {}
        for part in inner.split():
            key, sep, value = part.partition("=")
            if not key or not sep or not value:
                return {"action": "link", "error": f"invalid modifier {part!r}"}
            attrs[key] = value
        unsupported = [key for key in attrs if key != "action"]
        if unsupported:
            return {"action": attrs.get("action", "link"), "error": f"unsupported modifier {unsupported[0]!r}"}
        return {"action": attrs.get("action", "link")}

    def resolve_semantic_ref(self, token: SemanticRefToken) -> dict[str, Any]:
        if token.kind not in SEMANTIC_REF_SUPPORTED_KINDS:
            return {
                "target_kind": token.kind,
                "target_id": token.id,
                "target_key": f"{token.kind}:{token.id}",
                "target_href": "",
                "target_title": "",
                "target_status": "unsupported_kind",
                "exists": False,
                "linkable": False,
                "warning": f"unsupported semantic reference kind {token.kind!r}",
            }
        if token.kind == "work":
            return self.resolve_catalogue_ref(token, "works.json", "works", "work_id", 5, "/works")
        if token.kind == "series":
            return self.resolve_catalogue_ref(token, "series.json", "series", "series_id", 3, "/series", allow_slug_id=True)
        return self.resolve_catalogue_ref(token, "moments.json", "moments", "moment_id", None, "/moments", moment_id=True)

    def resolve_catalogue_ref(
        self,
        token: SemanticRefToken,
        filename: str,
        root_key: str,
        id_field: str,
        numeric_width: int | None,
        route_base: str,
        *,
        allow_slug_id: bool = False,
        moment_id: bool = False,
    ) -> dict[str, Any]:
        try:
            if moment_id:
                normalized_id = self.normalize_moment_id(token.id)
            elif allow_slug_id:
                normalized_id = self.normalize_semantic_series_id(token.id, numeric_width or 0)
            else:
                normalized_id = self.normalize_numeric_semantic_id(token.id, numeric_width or 0)
        except ValueError:
            return {
                "target_kind": token.kind,
                "target_id": token.id,
                "target_key": f"{token.kind}:{token.id}",
                "target_href": "",
                "target_title": "",
                "target_status": "invalid_id",
                "exists": False,
                "linkable": False,
                "warning": f"invalid semantic reference id {token.kind}:{token.id}",
            }
        records = self.load_catalogue_records(filename, root_key, id_field)
        record = records.get(normalized_id)
        target_key = f"{token.kind}:{normalized_id}"
        if not record:
            return {
                "target_kind": token.kind,
                "target_id": normalized_id,
                "target_key": target_key,
                "target_href": "",
                "target_title": "",
                "target_status": "missing",
                "exists": False,
                "linkable": False,
                "warning": f"unresolved semantic reference {target_key}",
            }
        status = str(record.get("status") or "").strip().lower() or "unknown"
        return {
            "target_kind": token.kind,
            "target_id": str(record.get(id_field) or normalized_id),
            "target_key": target_key,
            "target_href": self.catalogue_ref_href(token.kind, normalized_id, route_base),
            "target_title": str(record.get("title") or "").strip(),
            "target_status": status,
            "exists": True,
            "linkable": status == "published",
            "warning": "" if status == "published" else f"semantic reference {target_key} targets non-published catalogue record",
        }

    def catalogue_ref_href(self, kind: str, normalized_id: str, route_base: str) -> str:
        encoded_id = quote(normalized_id)
        if kind == "work":
            return f"/works/?work={encoded_id}"
        if kind == "series":
            return f"/series/?series={encoded_id}"
        return f"{route_base}/{encoded_id}/"

    def normalize_numeric_semantic_id(self, value: str, width: int) -> str:
        text = re.sub(r"\D", "", value.strip().removeprefix("'"))
        text = re.sub(r"\.0+\Z", "", text)
        if not text:
            raise ValueError("invalid id")
        return text.rjust(width, "0")

    def normalize_semantic_series_id(self, value: str, width: int) -> str:
        text = re.sub(r"\.0+\Z", "", value.strip().removeprefix("'"))
        if not text:
            raise ValueError("invalid series id")
        if re.fullmatch(r"\d+", text):
            return text.rjust(width, "0")
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
            return text
        raise ValueError("invalid series id")

    def normalize_moment_id(self, value: str) -> str:
        text = value.strip().lower().removesuffix(".md")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", text):
            raise ValueError("invalid moment id")
        return text

    def load_catalogue_records(self, filename: str, root_key: str, id_field: str) -> dict[str, dict[str, Any]]:
        cache_key = f"{filename}:{root_key}:{id_field}"
        if cache_key in self._catalogue_cache:
            return self._catalogue_cache[cache_key]
        path = self.repo_root / "studio" / "data" / "canonical" / "catalogue" / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._catalogue_cache[cache_key] = {}
            return {}
        records = payload.get(root_key)
        rows = records.values() if isinstance(records, dict) else records if isinstance(records, list) else []
        out: dict[str, dict[str, Any]] = {}
        for row in rows:
            if isinstance(row, dict):
                target_id = str(row.get(id_field) or "").strip()
                if target_id:
                    out[target_id] = row
        self._catalogue_cache[cache_key] = out
        return out

    def semantic_ref_warnings(self, token: SemanticRefToken, resolution: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        if token.modifier_error:
            warnings.append(token.modifier_error)
        if token.action not in SEMANTIC_REF_ALLOWED_ACTIONS:
            warnings.append(f"unsupported semantic reference action {token.action!r}")
        if resolution.get("warning"):
            warnings.append(str(resolution["warning"]))
        return warnings

    def warn_semantic_ref(self, doc: DocRecord, message: str) -> None:
        warning = f"Docs semantic reference warning [{self.scope_id}/{doc.doc_id}]: {message}"
        self.warnings.append(warning)
        print(warning, file=sys.stderr)

    def semantic_ref_label(self, token: SemanticRefToken, resolution: dict[str, Any]) -> str:
        return token.label or str(resolution.get("target_title") or "").strip() or str(resolution.get("target_key") or "")

    def semantic_ref_record(
        self,
        doc: DocRecord,
        token: SemanticRefToken,
        resolution: dict[str, Any],
        ordinal: int,
    ) -> dict[str, Any]:
        return {
            "source_scope": self.scope_id,
            "source_doc_id": doc.doc_id,
            "source_title": doc.title,
            "source_path": doc.source_path,
            "source_viewer_url": doc.viewer_url,
            "target_kind": resolution["target_kind"],
            "target_id": resolution["target_id"],
            "target_key": resolution["target_key"],
            "target_href": resolution["target_href"],
            "target_title": resolution.get("target_title", ""),
            "target_status": resolution["target_status"],
            "label": self.semantic_ref_label(token, resolution),
            "action": token.action,
            "ordinal": ordinal,
        }

    def render_semantic_ref_token(self, token: SemanticRefToken, resolution: dict[str, Any], usable: bool) -> str:
        label = html.escape(self.semantic_ref_label(token, resolution))
        attrs = {
            "data-ref-kind": resolution["target_kind"],
            "data-ref-id": resolution["target_id"],
            "data-ref-action": token.action,
        }
        if usable and resolution.get("linkable") and resolution.get("target_href"):
            attrs["target"] = "_blank"
            attrs["rel"] = "noopener noreferrer"
            return f'<a href="{html.escape(str(resolution["target_href"]), quote=True)}" {self.html_attrs(attrs)}>{label}</a>'
        attrs["data-ref-status"] = resolution["target_status"]
        return f"<span {self.html_attrs(attrs)}>{label}</span>"

    def html_attrs(self, attrs: dict[str, Any]) -> str:
        return " ".join(f'{key}="{html.escape(str(value), quote=True)}"' for key, value in attrs.items())

    @property
    def references_dir(self) -> Path:
        return self.output_dir / "references"

    @property
    def references_by_doc_dir(self) -> Path:
        return self.references_dir / "by-doc"

    @property
    def references_by_target_dir(self) -> Path:
        return self.references_dir / "by-target"

    def reference_target_path(self, target_kind: str, target_id: str) -> Path:
        return self.references_by_target_dir / str(target_kind) / f"{quote(str(target_id))}.json"

    def reference_target_url(self, target_kind: str, target_id: str) -> str:
        return f"{self.output_url_base}/references/by-target/{quote(str(target_kind))}/{quote(str(target_id))}.json"

    def build_reference_payloads(
        self,
        docs: list[DocRecord],
        semantic_references_by_doc: dict[str, list[dict[str, Any]]],
    ) -> dict[str, Any]:
        references = [ref for doc in docs for ref in semantic_references_by_doc.get(doc.doc_id, [])]
        by_doc = {
            doc_id: {
                "header": {
                    "schema": "docs_semantic_references_by_doc_v1",
                    "scope": self.scope_id,
                    "doc_id": doc_id,
                    "count": len(refs),
                },
                "references": refs,
            }
            for doc_id, refs in semantic_references_by_doc.items() if refs
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for ref in references:
            grouped.setdefault((str(ref["target_kind"]), str(ref["target_id"])), []).append(ref)
        by_target: dict[tuple[str, str], dict[str, Any]] = {}
        for key, refs in grouped.items():
            first = refs[0]
            by_target[key] = {
                "header": {
                    "schema": "docs_semantic_references_by_target_v1",
                    "scope": self.scope_id,
                    "count": len(refs),
                },
                "target_key": first["target_key"],
                "target_kind": key[0],
                "target_id": key[1],
                "target_href": first["target_href"],
                "target_title": first.get("target_title", ""),
                "target_status": first["target_status"],
                "count": len(refs),
                "references": sorted(
                    [
                        {
                            "source_scope": ref["source_scope"],
                            "source_doc_id": ref["source_doc_id"],
                            "source_title": ref["source_title"],
                            "source_path": ref["source_path"],
                            "source_viewer_url": ref["source_viewer_url"],
                            "label": ref["label"],
                            "action": ref["action"],
                            "ordinal": ref["ordinal"],
                        }
                        for ref in refs
                    ],
                    key=lambda ref: (ref["source_title"].lower(), ref["source_doc_id"], ref["ordinal"]),
                ),
            }
        targets = sorted(
            [
                {
                    "target_key": payload["target_key"],
                    "target_kind": payload["target_kind"],
                    "target_id": payload["target_id"],
                    "target_href": payload["target_href"],
                    "target_title": payload.get("target_title", ""),
                    "target_status": payload["target_status"],
                    "count": payload["count"],
                    "bucket_url": self.reference_target_url(payload["target_kind"], payload["target_id"]),
                }
                for payload in by_target.values()
            ],
            key=lambda target: (target["target_kind"], target["target_id"]),
        )
        comparable_index = {
            "header": {
                "schema": "docs_semantic_references_index_v1",
                "scope": self.scope_id,
                "count": len(references),
                "target_count": len(targets),
            },
            "targets": targets,
        }
        index_payload = {
            **comparable_index,
            "header": {
                **comparable_index["header"],
                "generated_at": self.effective_reference_generated_at(comparable_index),
            },
        }
        return {"index": index_payload, "by_doc": by_doc, "by_target": by_target}

    def effective_reference_generated_at(self, index_without_generated_at: dict[str, Any]) -> str:
        existing = read_json(self.references_dir / "index.json")
        if not isinstance(existing, dict):
            return utc_timestamp()
        header = dict(existing.get("header") or {})
        generated_at = str(header.pop("generated_at", "")).strip()
        comparable = {**existing, "header": header}
        if comparable == index_without_generated_at and generated_at:
            return generated_at
        return utc_timestamp()

    def existing_reference_records_by_doc(self, docs: list[DocRecord], target_doc_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        selected = set(target_doc_ids)
        out: dict[str, list[dict[str, Any]]] = {}
        for doc in docs:
            if doc.doc_id in selected:
                continue
            payload = read_json(self.references_by_doc_dir / f"{doc.doc_id}.json")
            refs = payload.get("references") if isinstance(payload, dict) else None
            if isinstance(refs, list):
                out[doc.doc_id] = refs
        return out

    def existing_doc_payload_ids(self, directory: Path) -> list[str]:
        if not directory.exists():
            return []
        return sorted(path.stem for path in directory.glob("*.json"))

    def existing_reference_target_keys(self) -> list[tuple[str, str]]:
        if not self.references_by_target_dir.exists():
            return []
        return sorted(
            (path.parent.name, unquote(path.stem))
            for path in self.references_by_target_dir.glob("*/*.json")
        )

    def build_write_plan(
        self,
        index_payload: dict[str, Any],
        item_payloads: dict[str, dict[str, Any]],
        reference_payloads: dict[str, Any],
        *,
        target_doc_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        index_text = json_text(index_payload)
        item_text_by_id: dict[str, str] = {}
        changed_item_ids: list[str] = []
        for doc_id, payload in item_payloads.items():
            text = json_text(payload)
            item_text_by_id[doc_id] = text
            if read_text(self.items_dir / f"{doc_id}.json") != text:
                changed_item_ids.append(doc_id)
        existing_item_ids = self.existing_doc_payload_ids(self.items_dir)
        desired_item_ids = sorted(item_payloads)
        stale_item_ids = sorted(set(existing_item_ids) - set(desired_item_ids))
        if target_doc_ids:
            stale_item_ids = sorted(set(stale_item_ids) & set(target_doc_ids))
        return {
            "index_write": read_text(self.output_dir / "index.json") != index_text,
            "index_text": index_text,
            "changed_item_ids": sorted(changed_item_ids),
            "stale_item_ids": stale_item_ids,
            "item_text_by_id": item_text_by_id,
            **self.build_reference_write_plan(reference_payloads, target_doc_ids=target_doc_ids),
        }

    def build_reference_write_plan(self, reference_payloads: dict[str, Any], *, target_doc_ids: list[str] | None) -> dict[str, Any]:
        reference_index_text = json_text(reference_payloads["index"])
        doc_text_by_id: dict[str, str] = {}
        changed_doc_ids: list[str] = []
        for doc_id, payload in reference_payloads["by_doc"].items():
            text = json_text(payload)
            doc_text_by_id[doc_id] = text
            if read_text(self.references_by_doc_dir / f"{doc_id}.json") != text:
                changed_doc_ids.append(doc_id)
        target_text_by_key: dict[tuple[str, str], str] = {}
        changed_target_keys: list[tuple[str, str]] = []
        for key, payload in reference_payloads["by_target"].items():
            text = json_text(payload)
            target_text_by_key[key] = text
            if read_text(self.reference_target_path(*key)) != text:
                changed_target_keys.append(key)
        stale_doc_ids = sorted(set(self.existing_doc_payload_ids(self.references_by_doc_dir)) - set(reference_payloads["by_doc"]))
        if target_doc_ids:
            target_set = set(target_doc_ids)
            changed_doc_ids = [doc_id for doc_id in changed_doc_ids if doc_id in target_set]
            stale_doc_ids = sorted(set(stale_doc_ids) & target_set)
        stale_target_keys = sorted(set(self.existing_reference_target_keys()) - set(reference_payloads["by_target"]))
        return {
            "reference_index_write": read_text(self.references_dir / "index.json") != reference_index_text,
            "reference_index_text": reference_index_text,
            "changed_reference_doc_ids": sorted(changed_doc_ids),
            "stale_reference_doc_ids": stale_doc_ids,
            "reference_doc_text_by_id": doc_text_by_id,
            "changed_reference_target_keys": sorted(changed_target_keys),
            "stale_reference_target_keys": stale_target_keys,
            "reference_target_text_by_key": target_text_by_key,
        }

    def write_outputs(self, write_plan: dict[str, Any], *, docs_total: int, reference_total: int) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["index_write"]:
            write_text(self.output_dir / "index.json", write_plan["index_text"])
        for doc_id in write_plan["changed_item_ids"]:
            write_text(self.items_dir / f"{doc_id}.json", write_plan["item_text_by_id"][doc_id])
        for doc_id in write_plan["stale_item_ids"]:
            (self.items_dir / f"{doc_id}.json").unlink(missing_ok=True)
        self.write_reference_outputs(write_plan)
        self.print_human_summary(
            write_plan,
            mode="write",
            docs_total=docs_total,
            reference_total=reference_total,
        )

    def write_reference_outputs(self, write_plan: dict[str, Any]) -> None:
        self.references_by_doc_dir.mkdir(parents=True, exist_ok=True)
        self.references_by_target_dir.mkdir(parents=True, exist_ok=True)
        if write_plan["reference_index_write"]:
            write_text(self.references_dir / "index.json", write_plan["reference_index_text"])
        for doc_id in write_plan["changed_reference_doc_ids"]:
            write_text(self.references_by_doc_dir / f"{doc_id}.json", write_plan["reference_doc_text_by_id"][doc_id])
        for doc_id in write_plan["stale_reference_doc_ids"]:
            (self.references_by_doc_dir / f"{doc_id}.json").unlink(missing_ok=True)
        for key in write_plan["changed_reference_target_keys"]:
            write_text(self.reference_target_path(*key), write_plan["reference_target_text_by_key"][key])
        for key in write_plan["stale_reference_target_keys"]:
            self.reference_target_path(*key).unlink(missing_ok=True)

    def print_dry_run(self, index_payload: dict[str, Any], reference_payloads: dict[str, Any], write_plan: dict[str, Any]) -> None:
        self.print_human_summary(
            write_plan,
            mode="dry-run",
            docs_total=len(index_payload["docs"]),
            reference_total=reference_payloads["index"]["header"]["count"],
        )

    def print_human_summary(
        self,
        write_plan: dict[str, Any],
        *,
        mode: str,
        docs_total: int,
        reference_total: int,
    ) -> None:
        doc_write_count = len(write_plan["changed_item_ids"])
        doc_remove_count = len(write_plan["stale_item_ids"])
        reference_write_count = (
            (1 if write_plan["reference_index_write"] else 0)
            + len(write_plan["changed_reference_doc_ids"])
            + len(write_plan["changed_reference_target_keys"])
        )
        reference_remove_count = (
            len(write_plan["stale_reference_doc_ids"])
            + len(write_plan["stale_reference_target_keys"])
        )
        index_write_count = (1 if write_plan["index_write"] else 0) + (1 if write_plan["reference_index_write"] else 0)
        verb = "would write" if mode == "dry-run" else "wrote"
        remove_verb = "would remove" if mode == "dry-run" else "removed"

        print(f"Docs build ({mode}) scope={self.scope_id}")
        print(f"  docs total: {docs_total}")
        print(f"  docs {verb}: {doc_write_count}")
        print(f"  docs {remove_verb}: {doc_remove_count}")
        print(f"  references total: {reference_total}")
        print(f"  references {verb}: {reference_write_count}")
        print(f"  references {remove_verb}: {reference_remove_count}")
        print(f"  indexes {verb}: {index_write_count}")
        print(f"  warnings: {len(self.warnings)}")

    def diagnostics_payload(
        self,
        *,
        docs: list[DocRecord],
        write_plan: dict[str, Any],
        elapsed_seconds: float,
        target_doc_ids: list[str] | None,
    ) -> dict[str, Any]:
        return {
            "scope": self.scope_id,
            "build_mode": "targeted" if target_doc_ids is not None else "full",
            "only_doc_ids": target_doc_ids or [],
            "source_files_scanned": self.source_files_scanned,
            "docs_emitted": len(docs),
            "doc_payloads_changed": len(write_plan["changed_item_ids"]),
            "doc_payloads_removed": len(write_plan["stale_item_ids"]),
            "reference_index_changed": 1 if write_plan["reference_index_write"] else 0,
            "reference_by_doc_payloads_changed": len(write_plan["changed_reference_doc_ids"]),
            "reference_by_doc_payloads_removed": len(write_plan["stale_reference_doc_ids"]),
            "reference_by_target_payloads_changed": len(write_plan["changed_reference_target_keys"]),
            "reference_by_target_payloads_removed": len(write_plan["stale_reference_target_keys"]),
            "warning_count": len(self.warnings),
            "warnings": self.warnings,
            "elapsed_seconds": elapsed_seconds,
        }

    def print_diagnostics(self, diagnostics: dict[str, Any]) -> None:
        print(f"Docs builder diagnostics: {json.dumps(diagnostics, ensure_ascii=False, separators=(',', ':'))}")


def raw_scope_items(repo_root: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scopes = payload.get("scopes") if isinstance(payload, dict) else None
    if not isinstance(scopes, list):
        return {}
    return {
        str(item.get("scope_id") or "").strip().lower(): item
        for item in scopes if isinstance(item, dict)
    }


def browser_docs_index_url(config: DocsScopeConfig) -> str:
    return f"/{config.output.as_posix().lstrip('/')}/index.json"


def browser_search_index_url(config: DocsScopeConfig) -> str:
    return f"/{config.search_output.as_posix().lstrip('/')}"


def browser_search_policy_payload(config: DocsScopeConfig) -> dict[str, Any]:
    return {
        "domain": "docs_viewer",
        "schema": f"search_index_{config.scope_id}_v1",
        "index_url": browser_search_index_url(config),
        "targeted_policy": "record_update",
        "targeted_operations": ["create", "update", "delete"],
    }


def docs_viewer_settings_payload(repo_root: Path, scope_ids: list[str]) -> dict[str, Any] | None:
    try:
        payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    settings = payload.get("docs_viewer") if isinstance(payload, dict) else None
    if not isinstance(settings, dict):
        return None
    settings = json.loads(json.dumps(settings))
    statuses = settings.get("ui_statuses_by_scope")
    if isinstance(statuses, dict):
        settings["ui_statuses_by_scope"] = {
            scope_id: value for scope_id, value in statuses.items() if scope_id in scope_ids
        }
    return settings


def browser_scope_config_payload(repo_root: Path, configs: list[DocsScopeConfig]) -> dict[str, Any]:
    raw_by_scope = raw_scope_items(repo_root)
    scope_ids = [config.scope_id for config in configs]
    payload = {
        "schema_version": DOCS_VIEWER_BROWSER_CONFIG_SCHEMA_VERSION,
        "default_scope_id": configs[0].scope_id if configs else "",
        "scopes": [
            {
                "scope_id": config.scope_id,
                "scope_type": config.scope_type,
                "meta": str(raw_by_scope.get(config.scope_id, {}).get("meta") or "").strip(),
                "viewer_base_url": normalize_viewer_base_url(config.viewer_base_url),
                "include_scope_param": config.include_scope_param is True,
                "default_doc_id": config.default_doc_id,
                "media_path_prefix": config.media_path_prefix.as_posix(),
                "index_url": browser_docs_index_url(config),
                "search_index_url": browser_search_index_url(config),
                "search": browser_search_policy_payload(config),
            }
            for config in configs
        ],
    }
    settings = docs_viewer_settings_payload(repo_root, scope_ids)
    if settings:
        payload["docs_viewer"] = settings
    return payload


def write_browser_config(repo_root: Path, configs: list[DocsScopeConfig], *, path: Path, label: str) -> None:
    text = json_text(browser_scope_config_payload(repo_root, configs))
    target = repo_root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_text(encoding="utf-8") == text:
        print(f"{label}: unchanged")
        return
    target.write_text(text, encoding="utf-8")
    print(f"{label}: wrote")


def public_readonly_configs(configs: list[DocsScopeConfig]) -> list[DocsScopeConfig]:
    return [
        config for config in configs
        if is_public_readonly_scope(
            viewer_base_url=config.viewer_base_url,
            include_scope_param=config.include_scope_param,
        )
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Docs Viewer generated document payloads.")
    parser.add_argument("--scope", action="append", default=[], help="Limit build to a named docs scope.")
    parser.add_argument("--source", help="Override docs source directory for a single selected scope.")
    parser.add_argument("--output", help="Override docs data output directory for a single selected scope.")
    parser.add_argument("--viewer-base-url", help="Override viewer page URL base for a single selected scope.")
    parser.add_argument("--only-doc-ids", help="Comma-separated doc ids for a targeted docs payload rebuild.")
    parser.add_argument("--diagnostics", action="store_true", help="Print machine-readable diagnostics for automation.")
    parser.add_argument("--write", action="store_true", help="Write generated files.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    configs_by_scope = load_docs_scope_configs(repo_root)
    requested_scopes = [scope.strip().lower() for scope in args.scope if scope.strip()]
    selected = [
        config for scope_id, config in configs_by_scope.items()
        if not requested_scopes or scope_id in requested_scopes
    ]
    if not selected:
        raise RuntimeError(f"Unknown docs scope(s): {', '.join(requested_scopes)}")
    if (args.source or args.output or args.viewer_base_url) and len(selected) != 1:
        raise RuntimeError("--source, --output, and --viewer-base-url can only be used when exactly one scope is selected")
    if args.only_doc_ids and len(selected) != 1:
        raise RuntimeError("--only-doc-ids can only be used when exactly one scope is selected")

    all_configs = list(configs_by_scope.values())
    if args.write:
        write_browser_config(
            repo_root,
            all_configs,
            path=DOCS_VIEWER_BROWSER_CONFIG_PATH,
            label="Docs Viewer browser config",
        )
        write_browser_config(
            repo_root,
            public_readonly_configs(all_configs),
            path=DOCS_VIEWER_PUBLIC_BROWSER_CONFIG_PATH,
            label="Docs Viewer public browser config",
        )
    only_doc_ids = None if args.only_doc_ids is None else [item.strip() for item in args.only_doc_ids.split(",") if item.strip()]
    for config in selected:
        builder = DocsDataBuilder(
            repo_root=repo_root,
            config=config,
            source_dir=Path(args.source) if args.source else None,
            output_dir=Path(args.output) if args.output else None,
            viewer_base_url=args.viewer_base_url,
            only_doc_ids=only_doc_ids,
        )
        builder.run(write=args.write, emit_diagnostics=args.diagnostics)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FrontMatterSyntaxError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)

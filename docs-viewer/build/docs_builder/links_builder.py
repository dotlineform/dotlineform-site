"""Document Build integration for the explicitly scoped Links pilot.

Sources own references. A private, rebuildable baseline survives builder process
restarts and is independent of the UI JSON schema. Writes complete synchronously;
the baseline advances only after all relationship writes/removals succeed.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Callable
from dataclasses import asdict
import fcntl
import json
from pathlib import Path
from typing import Any, TYPE_CHECKING
from urllib.parse import quote, unquote, urlsplit

from .common import json_text, render_markdown_to_html
from .links_model import DocumentLinks, DocumentTarget, Reference, Relationships, compare_links, relationship_views
from .links_schema import relationship_payload
from .semantic_tokens import replace_semantic_tokens
from docs_document_identity import is_immutable_doc_id
from docs_document_location import canonical_document_viewer_url, sub_scope_report_placement
from docs_document_subjects import FOLDER_PATH_FIELD, normalize_authoring_subject
from docs_rendered_links import collect_anchors, parse_docs_target, resolve_href
from docs_scope_config import DocsScopeConfig, document_source_path, generated_documents_path, load_docs_scope_configs, resolve_scope_path
from docs_source_model import load_document_collection_docs_for_config, write_text_atomic


CONFIG_PATH = Path("docs-viewer/config/links-builder.json")
Serializer = Callable[[Relationships, Mapping[DocumentTarget, DocumentLinks]], dict[str, Any]]

if TYPE_CHECKING:
    from .pipeline import DocsDataBuilder


def pilot_targets(repo_root: Path, config: DocsScopeConfig) -> set[DocumentTarget]:
    """Read the closed pilot boundary; no config or another scope/stage is a no-op."""
    path = repo_root / CONFIG_PATH
    if not path.is_file():
        return set()
    policy = json.loads(path.read_text())
    if policy["scope"] != config.scope_id or policy["stage"] != config.stage:
        return set()
    if config.stage != "working":
        raise ValueError("Links pilot requires an explicit Working stage")
    collections = {"", *(owner.sub_scope for owner in config.sub_scopes)}
    targets = set()
    identities = set()
    for row in policy["test_documents"]:
        key = DocumentTarget(config.scope_id, row["sub_scope"], row["doc_id"])
        if key.sub_scope not in collections or not is_immutable_doc_id(key.doc_id):
            raise ValueError("Links pilot requires exact configured document identities")
        if key.doc_id in identities:
            raise ValueError("Links pilot document IDs must be unique across collections")
        identities.add(key.doc_id)
        targets.add(key)
    return targets


def _safe_path(root: Path, name: str) -> Path:
    path = root / name
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Links builder output must stay inside its configured directory")
    return path


def load_link_documents(
    repo_root: Path, config: DocsScopeConfig, targets: set[DocumentTarget], *,
    pending_targets: Collection[DocumentTarget] = (),
) -> dict[DocumentTarget, DocumentLinks]:
    """Resolve exact sources, document existence and authored links inside the pilot."""
    owners = {"": config, **{owner.sub_scope: owner for owner in config.sub_scopes}}
    records, paths, locations, host_ids, payload_exists = {}, {}, {}, {}, {}
    by_id = {key.doc_id: key for key in targets}
    route_config = load_docs_scope_configs(repo_root, scope_ids=[config.scope_id])[config.scope_id]
    viewer_routes = tuple(sorted({(config.scope_id, config.viewer_base_url), (config.scope_id, route_config.viewer_base_url)}))
    for collection in sorted({key.sub_scope for key in targets}):
        owner = owners[collection]
        source_root = resolve_scope_path(repo_root, document_source_path(owner))
        output_root = resolve_scope_path(repo_root, generated_documents_path(owner)) / "by-id"
        host = sub_scope_report_placement(repo_root, config.scope_id, collection, stage=config.stage)[2] if collection else ""
        for key in targets:
            if key.sub_scope != collection:
                continue
            host_ids[key] = host
            locations[key] = canonical_document_viewer_url(config, host or key.doc_id, subdoc_id=key.doc_id if host else "")
        for doc in load_document_collection_docs_for_config(repo_root, config, owner):
            key = DocumentTarget(config.scope_id, collection, doc.doc_id)
            if key not in targets:
                continue
            if doc.path.is_symlink() or doc.path.resolve().parent != source_root.resolve():
                raise ValueError("Links source escaped its configured collection")
            records[key] = doc
            paths[doc.path.resolve()] = key
            payload_path = _safe_path(output_root, f"{key.doc_id}.json")
            payload_exists[key] = key in pending_targets or payload_path.is_file()
            if payload_path.is_file() and key not in pending_targets:
                payload = json.loads(payload_path.read_text())
                if payload.get("doc_id") != key.doc_id:
                    raise ValueError("Links target document payload identity does not match")

    documents = {}
    for key, doc in records.items():
        references = []
        markdown = replace_semantic_tokens(doc.body, registry=None, replacer=lambda token: "")
        for anchor in collect_anchors(render_markdown_to_html(markdown)):
            href = anchor["href"]
            if not href or href.startswith("#"):
                continue
            resolved = parse_docs_target(resolve_href(href, locations[key]), viewer_routes=viewer_routes)
            target = None
            if resolved and resolved["kind"] == "viewer" and resolved["scope"] == config.scope_id:
                target = by_id.get(resolved["subdoc"] or resolved["doc_id"])
                if target and (bool(target.sub_scope) != bool(resolved["subdoc"]) or (target.sub_scope and host_ids[target] != resolved["doc_id"])):
                    target = None
            elif resolved and resolved["kind"] == "source_markdown":
                raw = urlsplit(href)
                if not raw.scheme and not raw.netloc:
                    target = paths.get((doc.path.parent / unquote(raw.path)).resolve())
            if target is not None:
                fragment = resolved.get("fragment", "")
                occurrence_href = locations[target] + ("#" + quote(unquote(fragment), safe="-._~!$&'()*+,;=:@/?") if fragment else "")
                references.append(Reference(target, anchor["text"], occurrence_href))
        documents[key] = DocumentLinks(
            target=key, title=doc.title, href=locations[key],
            subject=normalize_authoring_subject(doc.front_matter, folder_supported=True),
            eligible=doc.publishable and FOLDER_PATH_FIELD not in doc.front_matter,
            exists=payload_exists[key], references=tuple(references),
        )
    return documents


def _read_baseline(path: Path) -> dict[DocumentTarget, DocumentLinks]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text())
    if payload["model_version"] != 1:
        raise ValueError("Unsupported Links builder baseline model")
    result = {}
    for row in payload["documents"]:
        fields = dict(row)
        fields["target"] = DocumentTarget(**row["target"])
        fields["references"] = tuple(Reference(DocumentTarget(**ref["target"]), ref["label"], ref["href"]) for ref in row["references"])
        doc = DocumentLinks(**fields)
        result[doc.target] = doc
    return result


def rebuild_links(
    repo_root: Path, config: DocsScopeConfig, targets: set[DocumentTarget], *,
    write: bool, serializer: Serializer = relationship_payload,
    pending_targets: Collection[DocumentTarget] = (),
) -> dict[str, Any]:
    """Reconcile the closed test graph; only changed relationship files are written.

    Reprojection on each invocation lets schema changes update existing output
    without reading the old UI schema. The private baseline is not publishable.
    Missing baseline/output is recovered from current configured sources.
    """
    output = resolve_scope_path(repo_root, generated_documents_path(config)) / "links-by-id"
    private = repo_root / "var/docs-viewer/links-builder" / config.scope_id / config.stage
    state_path = _safe_path(private, "state.json")
    before = {key: value for key, value in _read_baseline(state_path).items() if key in targets}
    documents = load_link_documents(repo_root, config, targets, pending_targets=pending_targets)
    changes = compare_links(before, documents)
    views = relationship_views(documents)
    writes, removals = {}, []
    for key in sorted(targets):
        path = _safe_path(output, f"{key.doc_id}.json")
        if key not in views:
            if path.exists():
                removals.append(path)
            continue
        content = json_text(serializer(views[key], documents))
        if not path.exists() or path.read_text() != content:
            writes[path] = content
    if write:
        for path, content in writes.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_text_atomic(path, content)
        for path in removals:
            path.unlink()
        state = json_text({"model_version": 1, "documents": [asdict(documents[key]) for key in sorted(documents)]})
        if not state_path.exists() or state_path.read_text() != state:
            private.mkdir(parents=True, exist_ok=True)
            write_text_atomic(state_path, state)
    return {
        "documents_changed": len(changes),
        "occurrences_added": sum(len(change.added) for change in changes.values()),
        "occurrences_deleted": sum(len(change.deleted) for change in changes.values()),
        "written": [path.name for path in writes],
        "removed": [path.name for path in removals],
    }


def build_document_links(
    builder: DocsDataBuilder, built_doc_ids: Collection[str], *, write: bool,
) -> dict[str, Any] | None:
    """Called by ordinary parent/child Doc Build, before its operation completes."""
    targets = pilot_targets(builder.repo_root, builder.config)
    collection = getattr(builder, "sub_scope_id", "")
    if not any(key.sub_scope == collection and key.doc_id in built_doc_ids for key in targets):
        return None
    owner = getattr(builder, "sub_scope_config", builder.config)
    if builder.source_dir != resolve_scope_path(builder.repo_root, document_source_path(owner)) or builder.output_dir != resolve_scope_path(builder.repo_root, generated_documents_path(owner)):
        raise ValueError("Links pilot requires the configured source and output locations")
    if not write:
        pending = {DocumentTarget(builder.scope_id, collection, doc_id) for doc_id in built_doc_ids}
        return rebuild_links(builder.repo_root, builder.config, targets, write=False, pending_targets=pending)
    private = builder.repo_root / "var/docs-viewer/links-builder" / builder.scope_id / builder.config.stage
    private.mkdir(parents=True, exist_ok=True)
    with _safe_path(private, "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = rebuild_links(builder.repo_root, builder.config, targets, write=True)
    print(f"  links: {len(result['written'])} written; {len(result['removed'])} removed; {result['occurrences_added']} occurrences added; {result['occurrences_deleted']} deleted")
    return result

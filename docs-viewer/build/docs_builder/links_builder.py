"""Document Build relationship maintenance for a configured Working scope.

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


def links_enabled(repo_root: Path, config: DocsScopeConfig) -> bool:
    """Enable all configured collections of the selected scope and Working stage."""
    path = repo_root / CONFIG_PATH
    if not path.is_file():
        return False
    policy = json.loads(path.read_text())
    if not isinstance(policy, dict) or set(policy) != {"scope", "stage"}:
        raise ValueError("Links configuration requires only scope and stage")
    if not isinstance(policy["scope"], str) or not policy["scope"] or policy["scope"] != policy["scope"].strip():
        raise ValueError("Links configuration requires an exact scope")
    if policy["stage"] != "working":
        raise ValueError("Links configuration requires an explicit Working stage")
    return policy["scope"] == config.scope_id and policy["stage"] == config.stage


def _safe_path(root: Path, name: str) -> Path:
    path = root / name
    if root.is_symlink() or path.is_symlink() or path.resolve().parent != root.resolve():
        raise ValueError("Links builder output must stay inside its configured directory")
    return path


def load_link_documents(
    repo_root: Path, config: DocsScopeConfig, *,
    pending_targets: Collection[DocumentTarget] = (),
) -> dict[DocumentTarget, DocumentLinks]:
    """Read every configured collection once and resolve exact authored links."""
    owners = {"": config, **{owner.sub_scope: owner for owner in config.sub_scopes}}
    records, paths, locations, host_ids, payload_exists = {}, {}, {}, {}, {}
    by_id = {}
    route_config = load_docs_scope_configs(repo_root, scope_ids=[config.scope_id])[config.scope_id]
    viewer_routes = tuple(sorted({(config.scope_id, config.viewer_base_url), (config.scope_id, route_config.viewer_base_url)}))
    for collection, owner in sorted(owners.items()):
        source_root = resolve_scope_path(repo_root, document_source_path(owner))
        output_root = resolve_scope_path(repo_root, generated_documents_path(owner)) / "by-id"
        docs = load_document_collection_docs_for_config(repo_root, config, owner)
        host = sub_scope_report_placement(repo_root, config.scope_id, collection, stage=config.stage)[2] if collection and docs else ""
        for doc in docs:
            key = DocumentTarget(config.scope_id, collection, doc.doc_id)
            if not is_immutable_doc_id(key.doc_id) or key.doc_id in by_id:
                raise ValueError("Links requires immutable document IDs unique across configured collections")
            by_id[key.doc_id] = key
            host_ids[key] = host
            locations[key] = canonical_document_viewer_url(config, host or key.doc_id, subdoc_id=key.doc_id if host else "")
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
    repo_root: Path, config: DocsScopeConfig, *,
    write: bool, serializer: Serializer = relationship_payload,
    pending_targets: Collection[DocumentTarget] = (),
) -> dict[str, Any]:
    """Reconcile all configured sources; write only changed relationship files.

    Reprojection on each invocation lets schema changes update existing output
    without reading the old UI schema. The private baseline is not publishable.
    Missing baseline/output is recovered from current configured sources.
    """
    output = resolve_scope_path(repo_root, generated_documents_path(config)) / "links-by-id"
    private = repo_root / "var/docs-viewer/links-builder" / config.scope_id / config.stage
    state_path = _safe_path(private, "state.json")
    before = _read_baseline(state_path)
    documents = load_link_documents(repo_root, config, pending_targets=pending_targets)
    changes = compare_links(before, documents)
    views = relationship_views(documents)
    writes = {}
    expected_ids = {key.doc_id for key in views}
    # The scope-owned directory must also recover from deletions without a baseline.
    removals = [
        _safe_path(output, path.name) for path in sorted(output.glob("*.json"))
        if is_immutable_doc_id(path.stem) and path.stem not in expected_ids
    ]
    for key in sorted(views):
        path = _safe_path(output, f"{key.doc_id}.json")
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
    if not links_enabled(builder.repo_root, builder.config):
        return None
    collection = getattr(builder, "sub_scope_id", "")
    owner = getattr(builder, "sub_scope_config", builder.config)
    if builder.source_dir != resolve_scope_path(builder.repo_root, document_source_path(owner)) or builder.output_dir != resolve_scope_path(builder.repo_root, generated_documents_path(owner)):
        raise ValueError("Links builder requires the configured source and output locations")
    if not write:
        pending = {DocumentTarget(builder.scope_id, collection, doc_id) for doc_id in built_doc_ids}
        return rebuild_links(builder.repo_root, builder.config, write=False, pending_targets=pending)
    private = builder.repo_root / "var/docs-viewer/links-builder" / builder.scope_id / builder.config.stage
    private.mkdir(parents=True, exist_ok=True)
    with _safe_path(private, "build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        result = rebuild_links(builder.repo_root, builder.config, write=True)
    print(f"  links: {len(result['written'])} written; {len(result['removed'])} removed; {result['occurrences_added']} occurrences added; {result['occurrences_deleted']} deleted")
    return result

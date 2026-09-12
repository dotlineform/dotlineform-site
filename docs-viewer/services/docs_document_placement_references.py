"""Preserve authored destinations when a document changes Working collection.

Only an explicit collection move inspects other source documents. Code and
comments are excluded, external/stage-qualified destinations retain their
meaning, and collection media is reused or copied without overwriting assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Iterator
import html
from pathlib import Path
import re
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit, unquote

from markdown_it import MarkdownIt

from docs_document_location import canonical_document_viewer_url, sub_scope_report_placement
from docs_document_placement import DocumentPlacement
from docs_management_document_target import resolve_managed_document_collection, confined_source_path
from docs_media_inventory import source_media_references
from docs_scope_config import resolve_location_path, load_docs_scope_configs
import docs_source_model as source_model

URL_PATTERN = re.compile(r"(?:[A-Za-z][A-Za-z0-9+.-]*://|//|/|docs/|\.\.?/)[^\s<>\"'\[\])|]+|[A-Za-z0-9_.-]+\.md(?:[?#][^\s<>\"'\[\])|]+)?")
MARKDOWN = MarkdownIt("commonmark")


@dataclass(frozen=True)
class MediaCopy:
    source: Path
    destination: Path
    content: bytes


@dataclass(frozen=True)
class ReferenceChange:
    sub_scope: str
    document: source_model.ScopeDoc
    body: str


def _inline_text_ranges(body: str, start: int, end: int) -> Iterator[tuple[int, int]]:
    """Exclude comments and matched backtick spans, including multiline spans."""
    cursor = start
    marker = re.compile(r"<!--|`+")
    while match := marker.search(body, cursor, end):
        opening = match.group()
        escaped = len(body[:match.start()]) - len(body[:match.start()].rstrip("\\"))
        if escaped % 2:
            cursor = match.end()
            continue
        if opening == "<!--":
            closing = body.find("-->", match.end(), end)
            after = end if closing < 0 else closing + 3
        else:
            closing = re.compile(r"(?<!`)" + opening + r"(?!`)").search(body, match.end(), end)
            if closing is None:
                cursor = match.end()
                continue
            after = closing.end()
        yield start, match.start()
        start = cursor = after
    yield start, end


def _reference_text_ranges(body: str) -> Iterator[tuple[int, int]]:
    offsets = [0]
    for line in body.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    cursor = 0
    for token in MARKDOWN.parse(body):
        literal = token.type in {"fence", "code_block"} or (
            token.type == "html_block" and token.content.lstrip().lower().startswith(("<pre", "<code", "<!--"))
        )
        if literal and token.map:
            start, end = (offsets[line] for line in token.map)
            yield from _inline_text_ranges(body, cursor, start)
            cursor = end
    yield from _inline_text_ranges(body, cursor, len(body))


def _rewrite_active_text(body: str, transform: Callable[[str], str]) -> str:
    edits = []
    for start, end in _reference_text_ranges(body):
        for match in URL_PATTERN.finditer(body, start, end):
            before = match.group()
            decoded = html.unescape(before)
            after = transform(decoded)
            if after == decoded:
                continue
            if "&amp;" in before:
                after = after.replace("&", "&amp;")
            if after != before:
                edits.append((match.start(), match.end(), after))
    for start, end, replacement in reversed(edits):
        body = body[:start] + replacement + body[end:]
    return body


def placement_reference_changes(
    repo_root: Path, placement: DocumentPlacement, body: str,
) -> tuple[str, list[ReferenceChange], list[MediaCopy]]:
    """Plan same-stage link rewrites and destination-owned media without writes."""
    source = placement.source
    destination = placement.destination
    config = source.parent_config
    route_config = load_docs_scope_configs(repo_root, scope_ids=[source.scope])[source.scope]
    routes = {owner.viewer_base_url.rstrip("/") for owner in (config, route_config)}
    collections = [resolve_managed_document_collection(
        repo_root, scope=source.scope, stage=source.stage, sub_scope=name or None,
    ) for name in ("", *(owner.sub_scope for owner in config.sub_scopes))]
    hosts = {owner.sub_scope: sub_scope_report_placement(
        repo_root, source.scope, owner.sub_scope, stage=source.stage,
    )[2] for owner in collections if owner.sub_scope}
    docs = [(owner, doc) for owner in collections for doc in source_model.load_document_collection_docs_for_config(
        repo_root, config, owner.document_config,
    )]
    by_path = {doc.path.resolve(): (owner.sub_scope, doc.doc_id) for owner, doc in docs}
    before_host = hosts.get(source.sub_scope, source.doc_id)
    after_host = hosts.get(destination.sub_scope, source.doc_id)

    def document_url(collection: str, doc_id: str) -> str:
        return canonical_document_viewer_url(config, hosts.get(collection, doc_id), subdoc_id=doc_id if collection else "")

    def rewrite_url(url: str, doc: source_model.ScopeDoc, moving: bool) -> str:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return url
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if params.get("stage", source.stage) != source.stage:
            return url
        if parsed.path.rstrip("/") in routes and params.get("scope", source.scope) == source.scope:
            if params.get("doc") != before_host:
                return url
            if (params.get("subdoc", "") != source.doc_id if source.sub_scope else bool(params.get("subdoc"))):
                return url
            params["doc"] = after_host
            if destination.sub_scope:
                params["subdoc"] = source.doc_id
            else:
                params.pop("subdoc", None)
            return urlunsplit(("", "", parsed.path, urlencode(params), parsed.fragment))
        if not parsed.path.startswith("/") and parsed.path.endswith(".md"):
            target_path = (doc.path.parent / unquote(parsed.path)).resolve()
            if target_path == source.document.path.resolve():
                target = document_url(destination.sub_scope, source.doc_id)
            elif moving and target_path in by_path:
                target = document_url(*by_path[target_path])
            else:
                return url
            target_parts = urlsplit(target)
            merged = dict(parse_qsl(target_parts.query))
            merged.update({key: value for key, value in params.items() if key not in {"scope", "doc", "subdoc"}})
            return urlunsplit(("", "", target_parts.path, urlencode(merged), parsed.fragment))
        return url

    changes = []
    for owner, doc in docs:
        if doc.path == source.document.path:
            continue
        rewritten = _rewrite_active_text(doc.body, lambda url: rewrite_url(url, doc, False))
        if rewritten != doc.body:
            changes.append(ReferenceChange(owner.sub_scope, doc, rewritten))
    body = _rewrite_active_text(body, lambda url: rewrite_url(url, source.document, True))
    body, copies = _relocate_media(repo_root, placement, body)
    return body, changes, copies


def _relocate_media(repo_root: Path, placement: DocumentPlacement, body: str) -> tuple[str, list[MediaCopy]]:
    source_owner = placement.source.document_config
    target_owner = placement.destination.document_config
    active = "\n".join(body[start:end] for start, end in _reference_text_ranges(body))
    active = _rewrite_active_text(active, lambda url: "" if urlsplit(url).scheme or urlsplit(url).netloc else url)
    references = source_media_references(source_owner, active.replace("|", " "), doc_id=placement.source.doc_id)
    copies: dict[Path, MediaCopy] = {}
    replacements: dict[str, str] = {}

    def copy_asset(source: Path, destination: Path) -> None:
        content = source.read_bytes()
        if destination.exists():
            if destination.is_symlink() or destination.read_bytes() != content:
                raise ValueError(f"Destination media already exists with different content: {destination.name}")
        if destination in copies and copies[destination].content != content:
            raise ValueError(f"Conflicting destination media: {destination.name}")
        copies[destination] = MediaCopy(source, destination, content)

    def asset_path(location, identity: str) -> Path:
        if location.provider not in {"repository", "external_local"}:
            raise ValueError("Working placement requires local collection media")
        root = resolve_location_path(repo_root, location).resolve()
        relative = Path(unquote(identity))
        if relative.is_absolute() or ".." in relative.parts or "\\" in identity:
            raise ValueError("Placement media escapes its configured root")
        candidate = root / relative
        if not root.is_dir() or any(path.is_symlink() for path in (candidate, *candidate.parents) if path.is_relative_to(root)):
            raise ValueError("Placement media requires an existing root and no symlinks")
        return candidate

    def copy_reference(media_type: str, identity: str) -> str:
        source_media = source_owner.media.types[media_type]
        target_media = target_owner.media.types.get(media_type)
        if target_media is None:
            raise ValueError(f"Destination does not support {media_type} media")
        copy_asset(asset_path(source_media.source_location, identity), asset_path(target_media.source_location, identity))
        for source_prefix, target_prefix in (
            (source_media.reference_prefix.as_posix(), target_media.reference_prefix.as_posix()),
            (source_media.served_path_prefix, target_media.served_path_prefix),
        ):
            replacements[f"{source_prefix}/{identity}"] = f"{target_prefix}/{identity}"
        for kind, build in source_owner.media.build_sources.items():
            if build.publishes_to != media_type:
                continue
            if kind != "mermaid":
                raise ValueError(f"Placement does not support media producer {kind}")
            build_identity = Path(identity).with_suffix(".mmd").as_posix()
            build_path = asset_path(build.location, build_identity)
            if build_path.is_file():
                target_build = target_owner.media.build_sources.get(kind)
                if target_build is None:
                    raise ValueError(f"Destination does not support media producer {kind}")
                copy_asset(build_path, asset_path(target_build.location, build_identity))
        return f"{target_media.served_path_prefix}/{identity}"

    for reference in references:
        copy_reference(reference.media_type, reference.identity)

    def rewrite_media(url: str) -> str:
        parsed = urlsplit(url)
        if parsed.scheme or parsed.netloc:
            return url
        path = parsed.path
        replacement = replacements.get(path)
        if replacement:
            return urlunsplit((parsed.scheme, parsed.netloc, replacement, parsed.query, parsed.fragment))
        # Resolve only configured source media. The viewer route stays /docs/,
        # so unrelated relative web links retain their original destination.
        if path.startswith(("../", "./")) and not path.endswith(".md"):
            original = (placement.source.document.path.parent / unquote(path)).resolve()
            for media_type, media in source_owner.media.types.items():
                root = resolve_location_path(repo_root, media.source_location).resolve()
                if original.is_relative_to(root):
                    identity = quote(original.relative_to(root).as_posix(), safe="/-._~")
                    confined_source_path(root, original)
                    return urlunsplit(("", "", copy_reference(media_type, identity), parsed.query, parsed.fragment))
        return url

    body = _rewrite_active_text(body, rewrite_media)
    return body, list(copies.values())

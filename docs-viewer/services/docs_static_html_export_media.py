#!/usr/bin/env python3
"""Plan and rewrite stage-owned media for static HTML snapshots."""

from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
from dataclasses import dataclass
from pathlib import Path
import unicodedata
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import SplitResult, quote, unquote, urlsplit

from docs_artifact_locations import (
    ArtifactLocationAdapter,
    RemoteArtifactClient,
    artifact_location_adapter,
    authenticated_remote_client_for_locations,
    normalize_artifact_identity,
)
from docs_workspace_config import DocsManagedMediaConfig


SIMPLE_URL_ATTRIBUTES = frozenset({"src", "poster", "data"})
SRCSET_ATTRIBUTE = "srcset"
HREF_ATTRIBUTE = "href"
EXTERNAL_HREF_ELEMENTS = frozenset({"link"})
IGNORED_DEPENDENCY_SCHEMES = frozenset({"blob", "data", "javascript", "mailto"})


@dataclass(frozen=True)
class OwnedMediaReference:
    media_type: str
    identity: str
    fragment: str


@dataclass(frozen=True)
class SnapshotMediaItem:
    media_type: str
    identity: str
    provider: str
    packaged_path: Path
    sha256: str
    doc_ids: tuple[str, ...]
    data: bytes

    def manifest_record(self) -> dict[str, Any]:
        return {
            "media_type": self.media_type,
            "identity": self.identity,
            "provider": self.provider,
            "packaged_path": self.packaged_path.as_posix(),
            "sha256": self.sha256,
            "doc_ids": list(self.doc_ids),
        }


@dataclass(frozen=True)
class SnapshotExternalDependency:
    reference: str
    element: str
    attribute: str
    doc_ids: tuple[str, ...]

    def manifest_record(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "element": self.element,
            "attribute": self.attribute,
            "doc_ids": list(self.doc_ids),
        }


@dataclass(frozen=True)
class SnapshotMediaPlan:
    items: tuple[SnapshotMediaItem, ...]
    external_dependencies: tuple[SnapshotExternalDependency, ...]
    rewritten_html_by_doc: Mapping[str, str]

    def manifest_records(self) -> list[dict[str, Any]]:
        return [item.manifest_record() for item in self.items]

    def external_dependency_records(self) -> list[dict[str, Any]]:
        return [item.manifest_record() for item in self.external_dependencies]


@dataclass(frozen=True)
class SrcsetCandidate:
    url: str
    descriptor: str


UrlTransform = Callable[[str, str, str], str]


class _HtmlUrlAttributeRewriter(HTMLParser):
    """Rewrite URL attributes while preserving text and non-tag HTML events."""

    def __init__(self, transform: UrlTransform, catalogue: Mapping[str, Any] | None = None) -> None:
        super().__init__(convert_charrefs=False)
        self.transform = transform
        self.parts: list[str] = []
        self.catalogue = catalogue
        self.elements: list[tuple[str, str, str]] = []

    def _start_tag(self, tag: str, attrs: list[tuple[str, str | None]], *, closed: bool) -> None:
        source_tag = tag
        if self.catalogue is not None:
            fields = dict(attrs)
            target = self.elements[-1][1] if self.elements else ""
            if "data-docs-media-kind" in fields:
                target = f'{fields["data-docs-media-kind"]}:{fields["data-docs-media-id"]}'
            if tag == "button" and "data-docs-media-open" in fields:
                attrs = [(name, value) for name, value in attrs if name not in {"type", "data-docs-media-open"}]
                if target.startswith("catalogue-work:"):
                    tag = "a"
                    attrs = [(name, value) for name, value in attrs if name != "style"]
                    attrs.append(("href", self.catalogue[target]["image"]["src"]))
                else:
                    tag = "span"
            if tag == "img" and target.startswith("catalogue-work:") and "data-docs-media-image" in fields:
                attrs = [(name, value) for name, value in attrs if name not in {"srcset", "sizes", "width", "height"}]
            if not closed and source_tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self.elements.append((source_tag, target, tag))
        self.parts.append(f"<{tag}")
        for name, value in attrs:
            self.parts.append(f" {name}")
            if value is None:
                continue
            rewritten = _transform_attribute_value(tag, name, value, self.transform)
            self.parts.append(f'="{html.escape(rewritten, quote=True)}"')
        self.parts.append("/>" if closed else ">")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start_tag(tag, attrs, closed=False)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._start_tag(tag, attrs, closed=True)

    def handle_endtag(self, tag: str) -> None:
        if self.catalogue is not None and self.elements and self.elements[-1][0] == tag:
            _source_tag, _target, tag = self.elements.pop()
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        self.parts.append(f"<!--{data}-->")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")

    def handle_pi(self, data: str) -> None:
        self.parts.append(f"<?{data}>")

    def unknown_decl(self, data: str) -> None:
        self.parts.append(f"<![{data}]>")


def parse_srcset(value: str) -> tuple[SrcsetCandidate, ...]:
    """Parse ordinary srcset candidates while keeping data-URL commas intact."""

    candidates: list[SrcsetCandidate] = []
    position = 0
    length = len(value)
    while position < length:
        while position < length and (value[position].isspace() or value[position] == ","):
            position += 1
        if position >= length:
            break
        url_start = position
        data_url = value[position : position + 5].lower() == "data:"
        while position < length and not value[position].isspace() and (data_url or value[position] != ","):
            position += 1
        url = value[url_start:position]
        while position < length and value[position].isspace():
            position += 1
        descriptor_start = position
        while position < length and value[position] != ",":
            position += 1
        descriptor = value[descriptor_start:position].strip()
        if url:
            candidates.append(SrcsetCandidate(url=url, descriptor=descriptor))
        if position < length:
            position += 1
    return tuple(candidates)


def render_srcset(candidates: Iterable[SrcsetCandidate]) -> str:
    return ", ".join(
        f"{candidate.url} {candidate.descriptor}" if candidate.descriptor else candidate.url
        for candidate in candidates
    )


def _transform_attribute_value(tag: str, name: str, value: str, transform: UrlTransform) -> str:
    attribute = name.lower()
    if attribute == SRCSET_ATTRIBUTE:
        return render_srcset(
            SrcsetCandidate(
                url=transform(tag.lower(), attribute, candidate.url),
                descriptor=candidate.descriptor,
            )
            for candidate in parse_srcset(value)
        )
    if attribute in SIMPLE_URL_ATTRIBUTES or attribute == HREF_ATTRIBUTE:
        return transform(tag.lower(), attribute, value)
    return value


def rewrite_html_url_attributes(html_text: str, transform: UrlTransform, *, catalogue: Mapping[str, Any] | None = None) -> str:
    parser = _HtmlUrlAttributeRewriter(transform, catalogue)
    parser.feed(html_text)
    parser.close()
    return "".join(parser.parts)


def _strict_path_identity(candidate_path: str, prefix_path: str) -> str | None:
    prefix = prefix_path.rstrip("/")
    if candidate_path == prefix:
        raise ValueError("stage-owned media reference must include a relative identity")
    if not candidate_path.startswith(f"{prefix}/"):
        return None
    decoded = unquote(candidate_path[len(prefix) + 1 :])
    if "\x00" in decoded:
        raise ValueError("stage-owned media identity contains a null byte")
    return normalize_artifact_identity(decoded)


def _prefix_match(candidate: SplitResult, prefix: SplitResult) -> str | None:
    if prefix.scheme or prefix.netloc:
        if (
            candidate.scheme.lower() != prefix.scheme.lower()
            or candidate.netloc.lower() != prefix.netloc.lower()
        ):
            return None
    elif candidate.scheme or candidate.netloc:
        return None
    return _strict_path_identity(candidate.path, prefix.path)


def _media_prefixes(
    media_configs: Mapping[str, DocsManagedMediaConfig],
) -> tuple[tuple[str, SplitResult], ...]:
    """Prepare configured logical prefixes once for this selected operation."""
    return tuple(
        (media_type, urlsplit("docs-media:" + media.served_path_prefix.removeprefix("/docs/assets/media/")))
        for media_type, media in sorted(media_configs.items())
    )


def owned_media_reference(
    value: str,
    prefixes: tuple[tuple[str, SplitResult], ...],
) -> OwnedMediaReference | None:
    raw = html.unescape(str(value or "").strip())
    if not raw or raw.startswith("#"):
        return None
    candidate = urlsplit(raw)
    for media_type, prefix in prefixes:
        identity = _prefix_match(candidate, prefix)
        if identity is not None:
            return OwnedMediaReference(
                media_type=media_type,
                identity=identity,
                fragment=candidate.fragment,
            )
    return None


def _dependency_reference(value: str) -> str:
    candidate = urlsplit(html.unescape(str(value or "").strip()))
    netloc = candidate.netloc
    if candidate.username is not None or candidate.password is not None:
        hostname = candidate.hostname or ""
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = f"{hostname}:{candidate.port}" if candidate.port is not None else hostname
    return candidate._replace(netloc=netloc, query="", fragment="").geturl()


def _is_external_dependency(element: str, attribute: str, value: str) -> bool:
    raw = html.unescape(str(value or "").strip())
    if not raw or raw.startswith("#"):
        return False
    candidate = urlsplit(raw)
    if candidate.scheme.lower() in IGNORED_DEPENDENCY_SCHEMES:
        return False
    if attribute == HREF_ATTRIBUTE:
        return element in EXTERNAL_HREF_ELEMENTS
    return attribute in SIMPLE_URL_ATTRIBUTES or attribute == SRCSET_ATTRIBUTE


def _portable_path_key(path: Path) -> str:
    return unicodedata.normalize("NFC", path.as_posix()).casefold()


def _packaged_media_url(packaged_path: Path, fragment: str) -> str:
    encoded_path = quote(packaged_path.as_posix(), safe="/-._~")
    return f"../{encoded_path}{f'#{fragment}' if fragment else ''}"


def _media_adapters(
    repo_root: Path,
    media_config: Mapping[str, DocsManagedMediaConfig],
    media_types: Iterable[str],
    *,
    remote_client: RemoteArtifactClient | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, ArtifactLocationAdapter]:
    selected = {
        media_type: media_config[media_type]
        for media_type in sorted(set(media_types))
    }
    client = authenticated_remote_client_for_locations(
        repo_root,
        [media.asset_location for media in selected.values()],
        client=remote_client,
        env_files=env_files,
        environ=environ,
    )
    return {
        media_type: artifact_location_adapter(
            repo_root,
            media.asset_location,
            served_path_prefix=media.served_path_prefix,
            remote_client=client,
        )
        for media_type, media in selected.items()
    }


def plan_snapshot_media(
    repo_root: Path,
    media_config: Mapping[str, DocsManagedMediaConfig],
    doc_payloads: Mapping[str, Mapping[str, Any]],
    *,
    remote_client: RemoteArtifactClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
    work_media: Mapping[str, Any] | None = None,
    work_assets: Any = None,
) -> SnapshotMediaPlan:
    prefixes = _media_prefixes(media_config)
    references: dict[tuple[str, str], set[str]] = {}
    dependencies: dict[tuple[str, str, str], set[str]] = {}
    packaged_paths: dict[tuple[str, str], Path] = {}
    packaged_keys: dict[str, tuple[str, str]] = {}
    rewritten_html: dict[str, str] = {}
    work_urls = {item.url: (item.binding, item.identity) for items in (work_media or {}).values() for item in items}

    for doc_id, payload in doc_payloads.items():
        owned_in_document = False

        def collect_and_rewrite(element: str, attribute: str, value: str) -> str:
            nonlocal owned_in_document
            owned = owned_media_reference(value, prefixes)
            if value in work_urls:
                media_type, identity = work_urls[value]
                owned = OwnedMediaReference(media_type, identity, "")
            if owned is not None:
                owned_in_document = True
                key = (owned.media_type, owned.identity)
                references.setdefault(key, set()).add(doc_id)
                if key not in packaged_paths:
                    packaged_path = Path("media") / owned.media_type / Path(owned.identity)
                    path_key = _portable_path_key(packaged_path)
                    existing = packaged_keys.get(path_key)
                    if existing is not None and existing != key:
                        raise ValueError("stage-owned media paths collide in the snapshot package")
                    packaged_keys[path_key] = key
                    packaged_paths[key] = packaged_path
                return _packaged_media_url(packaged_paths[key], owned.fragment)
            elif _is_external_dependency(element, attribute, value):
                reference = _dependency_reference(value)
                if reference:
                    dependencies.setdefault((reference, element, attribute), set()).add(doc_id)
            return value

        original_html = payload["content_html"]
        envelope = payload.get("catalogue")
        transformed_html = rewrite_html_url_attributes(original_html, collect_and_rewrite,
                                                       catalogue=envelope.get("presentations", {}) if envelope else None)
        rewritten_html[doc_id] = transformed_html if owned_in_document or envelope else original_html

    adapters = _media_adapters(
        repo_root,
        media_config,
        (media_type for media_type, _identity in references if media_type in media_config),
        remote_client=remote_client,
        env_files=env_files,
        environ=environ,
    )
    for media_type, location in (("catalogue/works/primary", work_assets.work_primary),
                                 ("catalogue/works/files", work_assets.work_files)) if work_assets else ():
        if any(kind == media_type for kind, _identity in references):
            adapters[media_type] = artifact_location_adapter(repo_root, location)
    items: list[SnapshotMediaItem] = []
    for media_type, identity in sorted(references):
        try:
            data = adapters[media_type].read(identity)
        except Exception as exc:
            raise ValueError(f"stage-owned media is unavailable: {media_type}/{identity}") from exc
        items.append(
            SnapshotMediaItem(
                media_type=media_type,
                identity=identity,
                provider=adapters[media_type].location.provider,
                packaged_path=packaged_paths[(media_type, identity)],
                sha256=hashlib.sha256(data).hexdigest(),
                doc_ids=tuple(sorted(references[(media_type, identity)])),
                data=data,
            )
        )
    external_dependencies = tuple(
        SnapshotExternalDependency(
            reference=reference,
            element=element,
            attribute=attribute,
            doc_ids=tuple(sorted(doc_ids)),
        )
        for (reference, element, attribute), doc_ids in sorted(dependencies.items())
    )
    return SnapshotMediaPlan(
        items=tuple(items),
        external_dependencies=external_dependencies,
        rewritten_html_by_doc=rewritten_html,
    )


__all__ = [
    "OwnedMediaReference",
    "SnapshotExternalDependency",
    "SnapshotMediaItem",
    "SnapshotMediaPlan",
    "SrcsetCandidate",
    "owned_media_reference",
    "parse_srcset",
    "plan_snapshot_media",
    "render_srcset",
    "rewrite_html_url_attributes",
]

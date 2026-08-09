#!/usr/bin/env python3
"""Plan and rewrite scope-owned media for static HTML snapshots."""

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
from docs_scope_config import DocsPublishedMediaConfig, DocsScopeConfig


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
    size: int
    sha256: str
    doc_ids: tuple[str, ...]
    data: bytes

    def manifest_record(self) -> dict[str, Any]:
        return {
            "media_type": self.media_type,
            "identity": self.identity,
            "provider": self.provider,
            "packaged_path": self.packaged_path.as_posix(),
            "size": self.size,
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

    @property
    def media_bytes(self) -> int:
        return sum(item.size for item in self.items)

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

    def __init__(self, transform: UrlTransform) -> None:
        super().__init__(convert_charrefs=False)
        self.transform = transform
        self.parts: list[str] = []

    def _start_tag(self, tag: str, attrs: list[tuple[str, str | None]], *, closed: bool) -> None:
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


def rewrite_html_url_attributes(html_text: str, transform: UrlTransform) -> str:
    parser = _HtmlUrlAttributeRewriter(transform)
    parser.feed(str(html_text or ""))
    parser.close()
    return "".join(parser.parts)


def _strict_path_identity(candidate_path: str, prefix_path: str) -> str | None:
    prefix = prefix_path.rstrip("/")
    if candidate_path == prefix:
        raise ValueError("scope-owned media reference must include a relative identity")
    if not candidate_path.startswith(f"{prefix}/"):
        return None
    decoded = unquote(candidate_path[len(prefix) + 1 :])
    if "\x00" in decoded:
        raise ValueError("scope-owned media identity contains a null byte")
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


def owned_media_reference(
    value: str,
    media_configs: Mapping[str, DocsPublishedMediaConfig],
) -> OwnedMediaReference | None:
    raw = html.unescape(str(value or "").strip())
    if not raw or raw.startswith("#"):
        return None
    candidate = urlsplit(raw)
    for media_type, media in sorted(media_configs.items()):
        prefix = urlsplit(media.served_path_prefix)
        if prefix.query or prefix.fragment:
            raise ValueError(f"configured served media prefix for {media_type} must not contain query or fragment")
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


def _packaged_media_url(item: SnapshotMediaItem, fragment: str) -> str:
    encoded_path = quote(item.packaged_path.as_posix(), safe="/-._~")
    return f"../{encoded_path}{f'#{fragment}' if fragment else ''}"


def _media_adapters(
    repo_root: Path,
    config: DocsScopeConfig,
    media_types: Iterable[str],
    *,
    remote_client: RemoteArtifactClient | None,
    env_files: Iterable[Path] | None,
    environ: Mapping[str, str] | None,
) -> dict[str, ArtifactLocationAdapter]:
    selected = {
        media_type: config.published.media[media_type]
        for media_type in sorted(set(media_types))
    }
    client = authenticated_remote_client_for_locations(
        repo_root,
        [media.location for media in selected.values()],
        client=remote_client,
        env_files=env_files,
        environ=environ,
    )
    return {
        media_type: artifact_location_adapter(
            repo_root,
            media.location,
            served_path_prefix=media.served_path_prefix,
            remote_client=client,
        )
        for media_type, media in selected.items()
    }


def plan_snapshot_media(
    repo_root: Path,
    config: DocsScopeConfig,
    doc_payloads: Mapping[str, Mapping[str, Any]],
    *,
    remote_client: RemoteArtifactClient | None = None,
    env_files: Iterable[Path] | None = None,
    environ: Mapping[str, str] | None = None,
) -> SnapshotMediaPlan:
    references: dict[tuple[str, str], set[str]] = {}
    dependencies: dict[tuple[str, str, str], set[str]] = {}

    for doc_id, payload in doc_payloads.items():
        def collect(element: str, attribute: str, value: str) -> str:
            owned = owned_media_reference(value, config.published.media)
            if owned is not None:
                references.setdefault((owned.media_type, owned.identity), set()).add(doc_id)
            elif _is_external_dependency(element, attribute, value):
                reference = _dependency_reference(value)
                if reference:
                    dependencies.setdefault((reference, element, attribute), set()).add(doc_id)
            return value

        rewrite_html_url_attributes(str(payload.get("content_html") or ""), collect)

    adapters = _media_adapters(
        repo_root,
        config,
        (media_type for media_type, _identity in references),
        remote_client=remote_client,
        env_files=env_files,
        environ=environ,
    )
    items: list[SnapshotMediaItem] = []
    packaged_keys: dict[str, tuple[str, str]] = {}
    for media_type, identity in sorted(references):
        try:
            data = adapters[media_type].read(identity)
        except Exception as exc:
            raise ValueError(f"scope-owned media is unavailable: {media_type}/{identity}") from exc
        packaged_path = Path("media") / media_type / Path(identity)
        path_key = _portable_path_key(packaged_path)
        existing = packaged_keys.get(path_key)
        if existing is not None and existing != (media_type, identity):
            raise ValueError("scope-owned media paths collide in the snapshot package")
        packaged_keys[path_key] = (media_type, identity)
        items.append(
            SnapshotMediaItem(
                media_type=media_type,
                identity=identity,
                provider=config.published.media[media_type].location.provider,
                packaged_path=packaged_path,
                size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
                doc_ids=tuple(sorted(references[(media_type, identity)])),
                data=data,
            )
        )
    items_by_identity = {(item.media_type, item.identity): item for item in items}
    owned_doc_ids = {doc_id for doc_ids in references.values() for doc_id in doc_ids}

    rewritten_html: dict[str, str] = {}
    for doc_id, payload in doc_payloads.items():
        original_html = str(payload.get("content_html") or "")
        if doc_id not in owned_doc_ids:
            rewritten_html[doc_id] = original_html
            continue

        def rewrite(_element: str, _attribute: str, value: str) -> str:
            owned = owned_media_reference(value, config.published.media)
            if owned is None:
                return value
            return _packaged_media_url(items_by_identity[(owned.media_type, owned.identity)], owned.fragment)

        rewritten_html[doc_id] = rewrite_html_url_attributes(
            original_html,
            rewrite,
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
